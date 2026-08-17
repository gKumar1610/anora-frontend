from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.db import init_db
from app import repository


class PromptUpdate(BaseModel):
    prompt: str = Field(min_length=20)


class ProfileUpdate(BaseModel):
    profile: dict[str, Any]


class TokenRequest(BaseModel):
    room_name: str | None = None
    participant_name: str | None = None


class TakeoverRequest(BaseModel):
    participant_identity: str = Field(min_length=1, max_length=100)


class OutboundCallPayload(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    guest_name: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Restaurant Voice Agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "livekit_configured": settings.has_livekit_credentials,
        "agent_name": settings.agent_name,
    }


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    return repository.get_metrics()


@app.get("/api/calls")
def calls(limit: int = 20) -> list[dict[str, Any]]:
    return repository.list_calls(limit=limit)


@app.get("/api/calls/{call_id}/transcript")
def transcript(call_id: str) -> list[dict[str, Any]]:
    return repository.list_transcript(call_id)


@app.get("/api/calls/{call_id}/events")
async def call_events(
    call_id: str,
    request: Request,
    after_id: int = 0,
    once: bool = False,
) -> StreamingResponse:
    if not repository.get_call(call_id):
        raise HTTPException(status_code=404, detail="Call not found.")

    async def stream():
        last_id = after_id
        while not await request.is_disconnected():
            rows = repository.list_transcript_since(call_id, last_id)
            for row in rows:
                last_id = max(last_id, int(row["id"]))
                yield f"event: transcript\ndata: {json.dumps(row, sort_keys=True)}\n\n"
            if once:
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/calls/outbound")
async def outbound_call(payload: OutboundCallPayload) -> dict[str, Any]:
    raise HTTPException(
        status_code=410,
        detail=(
            "Outbound calling is disabled for the LiveKit Phone Numbers setup. "
            "Configure a separate outbound SIP trunk before re-enabling this endpoint."
        ),
    )


@app.get("/api/bookings")
def bookings(limit: int = 50) -> list[dict[str, Any]]:
    return repository.list_bookings(limit=limit)


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    return {
        "system_prompt": repository.get_setting("system_prompt"),
        "restaurant_profile": repository.get_restaurant_profile(),
    }


@app.put("/api/settings/prompt")
def update_prompt(payload: PromptUpdate) -> dict[str, Any]:
    row = repository.set_setting("system_prompt", payload.prompt)
    return {"system_prompt": row["value"], "updated_at": row["updated_at"]}


@app.put("/api/settings/profile")
def update_profile(payload: ProfileUpdate) -> dict[str, Any]:
    row = repository.set_setting("restaurant_profile", json.dumps(payload.profile, indent=2))
    return {"restaurant_profile": json.loads(row["value"]), "updated_at": row["updated_at"]}


@app.post("/api/token", status_code=201)
def token(payload: TokenRequest) -> dict[str, str]:
    if not settings.has_livekit_credentials:
        raise HTTPException(
            status_code=503,
            detail="LiveKit credentials are missing. Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET.",
        )
    try:
        from livekit import api
    except Exception as exc:  # pragma: no cover - depends on optional runtime package
        raise HTTPException(status_code=500, detail=f"livekit-api is not installed: {exc}") from exc

    room_name = payload.room_name or f"demo-{uuid.uuid4().hex[:8]}"
    participant_name = payload.participant_name or "Owner demo"
    participant_identity = f"owner-{uuid.uuid4().hex[:8]}"
    room_config = api.RoomConfiguration(
        agents=[
            api.RoomAgentDispatch(
                agent_name=settings.agent_name,
                metadata=json.dumps({"source": "browser-demo", "room": room_name}),
            )
        ]
    )
    participant_token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(participant_identity)
        .with_name(participant_name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .with_room_config(room_config)
        .to_jwt()
    )
    return {"server_url": settings.livekit_url, "participant_token": participant_token}


def _require_livekit_api():
    if not settings.has_livekit_credentials:
        raise HTTPException(
            status_code=503,
            detail="LiveKit credentials are missing. Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET.",
        )
    try:
        from livekit import api
    except Exception as exc:  # pragma: no cover - depends on optional runtime package
        raise HTTPException(status_code=500, detail=f"livekit-api is not installed: {exc}") from exc
    return api


def _get_active_call(call_id: str) -> dict[str, Any]:
    call = repository.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")
    if call.get("status") not in repository.ACTIVE_CALL_STATUSES:
        raise HTTPException(status_code=409, detail="Call is not active.")
    if not call.get("room_name"):
        raise HTTPException(status_code=409, detail="Call room is missing.")
    return call


@app.post("/api/calls/{call_id}/jump-in-token", status_code=201)
def jump_in_token(call_id: str) -> dict[str, str]:
    call = _get_active_call(call_id)
    api = _require_livekit_api()
    participant_identity = f"owner-{uuid.uuid4().hex[:8]}"
    participant_token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(participant_identity)
        .with_name("Owner")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=call["room_name"],
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )
    return {
        "server_url": settings.livekit_url,
        "participant_token": participant_token,
        "room_name": call["room_name"],
        "participant_identity": participant_identity,
    }


@app.post("/api/calls/{call_id}/takeover")
async def takeover_call(call_id: str, payload: TakeoverRequest) -> dict[str, Any]:
    call = _get_active_call(call_id)
    api = _require_livekit_api()
    updated = repository.mark_owner_joined(call_id, payload.participant_identity)
    lkapi = api.LiveKitAPI()
    removed_agents: list[str] = []
    try:
        participants = await lkapi.room.list_participants(
            api.ListParticipantsRequest(room=call["room_name"])
        )
        for participant in participants.participants:
            if participant.kind != api.ParticipantInfo.AGENT:
                continue
            await lkapi.room.remove_participant(
                api.RoomParticipantIdentity(
                    room=call["room_name"],
                    identity=participant.identity,
                )
            )
            removed_agents.append(participant.identity)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not complete LiveKit takeover: {exc}") from exc
    finally:
        aclose = getattr(lkapi, "aclose", None)
        if aclose:
            await aclose()

    if removed_agents:
        updated = repository.mark_agent_removed(call_id)
    return {"call": updated, "removed_agents": removed_agents}


@app.post("/api/calls/{call_id}/end")
async def end_call(call_id: str) -> dict[str, Any]:
    call = repository.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found.")
    if call.get("status") == "completed":
        return {"call": call, "room_deleted": False}

    room_deleted = False
    if call.get("room_name"):
        api = _require_livekit_api()
        lkapi = api.LiveKitAPI()
        try:
            await lkapi.room.delete_room(api.DeleteRoomRequest(room=call["room_name"]))
            room_deleted = True
        except Exception as exc:
            message = getattr(exc, "message", None) or str(exc)
            lowered = message.lower()
            if "not found" not in lowered and "does not exist" not in lowered:
                raise HTTPException(status_code=502, detail=f"Could not end LiveKit room: {message}") from exc
        finally:
            aclose = getattr(lkapi, "aclose", None)
            if aclose:
                await aclose()

    repository.end_call(call_id)
    return {"call": repository.get_call(call_id), "room_deleted": room_deleted}


@app.get("/api/events")
async def events(request: Request) -> StreamingResponse:
    async def stream():
        previous = ""
        while not await request.is_disconnected():
            snapshot = {
                "metrics": repository.get_metrics(),
                "calls": repository.list_calls(limit=12),
                "bookings": repository.list_bookings(limit=12),
            }
            encoded = json.dumps(snapshot, sort_keys=True)
            if encoded != previous:
                yield f"event: snapshot\ndata: {encoded}\n\n"
                previous = encoded
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/{path:path}")
def serve_frontend(path: str) -> FileResponse:
    index = frontend_dist / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(
        status_code=404,
        detail="Frontend build not found. Run `cd frontend && npm install && npm run build`.",
    )
