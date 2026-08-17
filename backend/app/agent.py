from __future__ import annotations

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv
from google.protobuf.duration_pb2 import Duration

from app import repository
from app.config import AGENT_NAME as CONFIG_AGENT_NAME
from app.config import settings
from app.pipeline_logging import VoicePipelineLogger, log_transcript_event
from app.reservations import check_availability as check_slot
from app.reservations import create_confirmed_booking


load_dotenv(".env.local")
logger = logging.getLogger("restaurant-agent")
logging.basicConfig(level=logging.WARNING, format="%(message)s")

DEFAULT_CEREBRAS_MODEL = "gemma-4-31b"
DEFAULT_CARTESIA_STT_MODEL = "ink-whisper"
DEFAULT_CARTESIA_TTS_MODEL = "sonic-3"
DEFAULT_CARTESIA_TTS_VOICE = "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
AGENT_NAME = CONFIG_AGENT_NAME


try:
    from livekit import agents, api, rtc
    from livekit.agents import (
        Agent,
        AgentServer,
        AgentSession,
        RunContext,
        TurnHandlingOptions,
        function_tool,
        room_io,
    )
    from livekit.agents.beta.tools import EndCallTool
    from livekit.agents.llm import FallbackAdapter
    from livekit.plugins import ai_coustics, cartesia, cerebras, openai, silero
    from livekit.plugins.turn_detector.multilingual import MultilingualModel
except Exception as exc:  # pragma: no cover - exercised only when LiveKit deps are absent
    agents = None
    api = None
    rtc = None
    Agent = object
    AgentServer = None
    AgentSession = None
    RunContext = object
    TurnHandlingOptions = None
    function_tool = None
    room_io = None
    EndCallTool = None
    FallbackAdapter = None
    ai_coustics = None
    cartesia = None
    cerebras = None
    openai = None
    silero = None
    MultilingualModel = None
    LIVEKIT_IMPORT_ERROR = exc
else:
    LIVEKIT_IMPORT_ERROR = None


if function_tool is not None:

    class RestaurantReservationAgent(Agent):
        def __init__(self, call_id: str | None = None, default_phone: str | None = None) -> None:
            self.call_id = call_id
            self.default_phone = default_phone
            end_call_tool = EndCallTool(
                extra_description="Only end the call after the guest's booking request is complete or they clearly want to leave.",
                delete_room=True,
                end_instructions="Thank the guest warmly and say goodbye.",
            )
            # The model has no clock: without this it guesses the year when the
            # caller says "today" (observed booking 2025-07-05 on 2026-07-05).
            now = datetime.now(ZoneInfo("Asia/Kolkata"))
            date_context = (
                f"\n\nCurrent date and time: {now.strftime('%A, %Y-%m-%d %H:%M')} (Asia/Kolkata). "
                "Resolve relative dates like 'today' or 'tomorrow' from this."
            )
            super().__init__(
                instructions=repository.get_setting("system_prompt") + date_context,
                tools=end_call_tool.tools,
            )

        @function_tool()
        async def list_booking_policy(self, context: RunContext) -> dict[str, Any]:
            """Return the restaurant profile, opening hours, and booking policy."""
            return repository.get_restaurant_profile()

        @function_tool()
        async def check_availability(
            self,
            context: RunContext,
            party_size: int,
            reservation_date: str,
            reservation_time: str,
        ) -> dict[str, Any]:
            """Check whether a table is available for a party on a date and time.

            Args:
                party_size: Number of guests.
                reservation_date: Reservation date in YYYY-MM-DD.
                reservation_time: Reservation time in 24-hour HH:MM.
            """
            try:
                availability = check_slot(party_size, reservation_date, reservation_time)
            except ValueError as exc:
                # The model sometimes calls this before collecting a date/time.
                # Return a structured result so it asks the guest for the
                # missing detail instead of crashing the tool.
                return {
                    "available": False,
                    "reason": str(exc),
                    "needs_more_info": True,
                    "suggested_times": [],
                }
            return {
                "available": availability.available,
                "reason": availability.reason,
                "suggested_times": availability.suggested_times,
            }

        @function_tool()
        async def create_booking(
            self,
            context: RunContext,
            guest_name: str,
            phone: str,
            party_size: int,
            reservation_date: str,
            reservation_time: str,
            notes: str = "",
        ) -> dict[str, Any]:
            """Create a confirmed restaurant booking after details are collected.

            Args:
                guest_name: Guest's full name.
                phone: Best contact phone number. Use the caller's phone number when they say to use this number.
                party_size: Number of guests.
                reservation_date: Reservation date in YYYY-MM-DD.
                reservation_time: Reservation time in 24-hour HH:MM.
                notes: Optional notes, occasion, seating preference, or allergies.
            """
            try:
                booking = create_confirmed_booking(
                    guest_name=guest_name,
                    phone=phone or self.default_phone,
                    party_size=party_size,
                    reservation_date=reservation_date,
                    reservation_time=reservation_time,
                    notes=notes,
                    call_id=self.call_id,
                )
            except ValueError as exc:
                # Missing/invalid details or an unavailable slot. Report it back
                # so the model can ask for a correction instead of crashing.
                return {
                    "booked": False,
                    "reason": str(exc),
                }
            return {
                "confirmation_code": booking["confirmation_code"],
                "guest_name": booking["guest_name"],
                "party_size": booking["party_size"],
                "reservation_date": booking["reservation_date"],
                "reservation_time": booking["reservation_time"],
                "status": booking["status"],
            }

else:
    RestaurantReservationAgent = None


def _metadata_from_job(ctx: Any) -> dict[str, Any]:
    raw = getattr(getattr(ctx, "job", None), "metadata", "") or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def prewarm(proc: Any) -> None:
    proc.userdata["vad"] = silero.VAD.load()


def require_provider_keys() -> None:
    missing = [
        key
        for key in ("CEREBRAS_API_KEY", "CARTESIA_API_KEY")
        if not os.getenv(key)
    ]
    if missing:
        raise RuntimeError(
            "Missing provider API keys for the voice pipeline: "
            + ", ".join(missing)
            + ". Add them to .env.local."
        )


async def on_session_end(ctx: Any) -> None:
    if repository.is_owner_handoff_room(ctx.room.name):
        return
    repository.end_call_by_room(ctx.room.name)


def build_agent_session(ctx: Any, pipeline_logger: VoicePipelineLogger | None = None) -> Any:
    stt = cartesia.STT(
        model=os.getenv("CARTESIA_STT_MODEL", DEFAULT_CARTESIA_STT_MODEL),
        language=os.getenv("LIVEKIT_STT_LANGUAGE", "en"),
    )
    _llm_timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    _cerebras_model = os.getenv("CEREBRAS_MODEL", DEFAULT_CEREBRAS_MODEL)
    _llm_kwargs: dict[str, Any] = {}
    if _cerebras_model.startswith("gpt-oss"):
        # gpt-oss is a reasoning model; keep hidden reasoning short so the
        # first spoken token arrives fast. NOTE: gpt-oss-120b degenerates when
        # tools are attached (repeats the same question many times in one
        # reply, reproduced 4/4 against the live API), which is why it is not
        # the default. gemma-4-31b is: it replays cleanly with the tool schema
        # attached and is ~3x terser than zai-glm-4.7 (33 vs 105 output
        # tokens/turn), which cuts both LLM and Cartesia TTS cost.
        _llm_kwargs["reasoning_effort"] = os.getenv("CEREBRAS_REASONING_EFFORT", "low")
    cerebras_llm = cerebras.LLM(
        model=_cerebras_model,
        # Bound the request so a stalled response fails fast and LiveKit can
        # recover, instead of hanging the turn indefinitely. This is an
        # httpx.Timeout, not a bare float.
        timeout=httpx.Timeout(_llm_timeout_seconds),
        temperature=float(os.getenv("CEREBRAS_TEMPERATURE", "0.2")),
        **_llm_kwargs,
    )
    # The Cerebras key has a tight requests-per-minute quota; mid-call 429s
    # killed a live call. Fall back to OpenAI when Cerebras is exhausted so
    # the agent keeps talking instead of going silent.
    inner_llms = [cerebras_llm]
    if os.getenv("OPENAI_API_KEY"):
        inner_llms.append(
            openai.LLM(
                model=os.getenv("FALLBACK_OPENAI_MODEL", "gpt-4.1-mini"),
                timeout=httpx.Timeout(_llm_timeout_seconds),
            )
        )
    llm = FallbackAdapter(inner_llms) if len(inner_llms) > 1 else cerebras_llm
    tts = cartesia.TTS(
        model=os.getenv("CARTESIA_TTS_MODEL", DEFAULT_CARTESIA_TTS_MODEL),
        voice=os.getenv("CARTESIA_TTS_VOICE", DEFAULT_CARTESIA_TTS_VOICE),
        language=os.getenv("LIVEKIT_TTS_LANGUAGE", "en"),
    )
    if pipeline_logger is not None:
        # Attach to the inner LLMs, not the adapter: metrics events are
        # emitted by the concrete plugins.
        pipeline_logger.attach_model_plugins(stt, *inner_llms, tts)

    return AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=stt,
        llm=llm,
        tts=tts,
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
            # Preemptive generation fires an extra LLM request per turn, which
            # roughly doubles our burn against the Cerebras RPM quota.
            preemptive_generation={"enabled": os.getenv("PREEMPTIVE_GENERATION", "0") == "1"},
        ),
        # Cartesia does not return TTS-aligned transcripts; leaving this on
        # just logs a warning every turn.
        use_tts_aligned_transcript=False,
    )


def _call_metadata(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    return value if isinstance(value, str) else ""


def _sip_status(exc: Exception) -> tuple[str, str | None]:
    metadata = getattr(exc, "metadata", {}) or {}
    message = getattr(exc, "message", None) or str(exc)
    return message, metadata.get("sip_status_code")


async def _start_session(
    session: Any,
    ctx: Any,
    assistant: Any,
    use_agent_audio_enhancement: bool,
) -> None:
    if use_agent_audio_enhancement:
        await session.start(
            room=ctx.room,
            agent=assistant,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=ai_coustics.audio_enhancement(
                        model=ai_coustics.EnhancerModel.QUAIL_VF_S
                    ),
                ),
            ),
        )
        return

    await session.start(room=ctx.room, agent=assistant)


def _is_sip_participant(participant: Any) -> bool:
    return getattr(participant, "kind", None) == rtc.ParticipantKind.PARTICIPANT_KIND_SIP


def attach_session_observers(session: Any, call_id: str, pipeline_logger: VoicePipelineLogger) -> None:
    def record_conversation(event: Any) -> None:
        item = getattr(event, "item", None)
        role = getattr(item, "role", None) or "agent"
        content = getattr(item, "content", None)
        if isinstance(content, list):
            text = " ".join(str(part) for part in content if part)
        else:
            text = str(content or "")
        if text.strip():
            speaker = "caller" if role == "user" else "agent"
            repository.add_transcript_event(call_id, speaker, text, True)
            log_transcript_event(speaker, text)

    try:
        session.on("conversation_item_added", record_conversation)
        pipeline_logger.attach_session(session)
    except Exception:
        logger.info("session event hooks unavailable in this SDK version")


def attach_call_lifecycle_logging(ctx: Any, pipeline_logger: VoicePipelineLogger) -> None:
    pipeline_logger.attach_room(ctx.room, is_caller_participant=_is_sip_participant)
    pipeline_logger.register_shutdown(ctx)


async def _capture_inbound_participant_metadata(
    ctx: Any,
    call_id: str,
    assistant: Any,
    pipeline_logger: VoicePipelineLogger,
) -> None:
    try:
        participant = await ctx.wait_for_participant()
    except Exception:
        logger.exception("failed to read inbound participant metadata")
        return

    if not _is_sip_participant(participant):
        return

    pipeline_logger.mark_caller_joined(participant)
    caller_number = participant.attributes.get("sip.phoneNumber")
    twilio_call_sid = participant.attributes.get("sip.twilio.callSid")
    assistant.default_phone = caller_number or assistant.default_phone
    repository.start_call(
        call_id=call_id,
        room_name=ctx.room.name,
        caller_number=caller_number,
        from_number=caller_number,
        twilio_call_sid=twilio_call_sid,
        direction="inbound",
    )


async def start_inbound_session(ctx: Any, metadata: dict[str, Any]) -> None:
    call_id = ctx.room.name
    pipeline_logger = VoicePipelineLogger(call_id=call_id, room_name=ctx.room.name, direction="inbound")
    repository.start_call(
        call_id=call_id,
        room_name=ctx.room.name,
        direction="inbound",
    )

    assistant = RestaurantReservationAgent(call_id=call_id)
    session = build_agent_session(ctx, pipeline_logger=pipeline_logger)
    attach_session_observers(session, call_id, pipeline_logger)
    attach_call_lifecycle_logging(ctx, pipeline_logger)

    is_browser_demo = metadata.get("source") == "browser-demo"

    await _start_session(
        session=session,
        ctx=ctx,
        assistant=assistant,
        use_agent_audio_enhancement=is_browser_demo,
    )

    if not is_browser_demo:
        # Wait for the SIP caller to actually join before greeting. Previously
        # the greeting fired immediately while participant capture ran as a
        # detached task, so on a slow room connect the agent spoke before the
        # caller's audio path existed and the greeting was never heard.
        # Awaiting the join makes the greeting reliable. Bounded so a stuck
        # join can never hang the call. Browser-demo callers skip this
        # entirely — there's no SIP participant to capture, and waiting here
        # left the call sitting in "listening" for up to the full timeout
        # before the agent ever spoke.
        try:
            await asyncio.wait_for(
                _capture_inbound_participant_metadata(ctx, call_id, assistant, pipeline_logger),
                timeout=float(os.getenv("CALLER_JOIN_TIMEOUT_SECONDS", "15")),
            )
        except asyncio.TimeoutError:
            logger.warning("caller did not join within timeout; greeting anyway")

    # No instructions override here: the agent's own system prompt already
    # defines its welcome message. Overriding it here previously spoke the
    # old restaurant greeting regardless of what the configured prompt said.
    await session.generate_reply()


async def start_outbound_session(ctx: Any, metadata: dict[str, Any]) -> None:
    phone_number = _call_metadata(metadata, "phone_number")
    from_number = _call_metadata(metadata, "from_number") or settings.sip_outbound_from_number
    call_id = _call_metadata(metadata, "call_id") or ctx.room.name
    guest_name = _call_metadata(metadata, "guest_name")
    notes = _call_metadata(metadata, "notes")

    repository.start_call(
        call_id=call_id,
        room_name=ctx.room.name,
        caller_number=phone_number,
        direction="outbound",
        from_number=from_number,
        to_number=phone_number,
        status="dialing",
    )

    pipeline_logger = VoicePipelineLogger(call_id=call_id, room_name=ctx.room.name, direction="outbound")
    assistant = RestaurantReservationAgent(call_id=call_id, default_phone=phone_number)
    session = build_agent_session(ctx, pipeline_logger=pipeline_logger)
    attach_session_observers(session, call_id, pipeline_logger)
    attach_call_lifecycle_logging(ctx, pipeline_logger)

    session_started = asyncio.create_task(
        _start_session(
            session=session,
            ctx=ctx,
            assistant=assistant,
            use_agent_audio_enhancement=False,
        )
    )

    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=settings.sip_outbound_trunk_id,
                sip_call_to=phone_number,
                sip_number=from_number,
                participant_identity=phone_number,
                participant_name=guest_name or "Restaurant guest",
                participant_metadata=json.dumps(
                    {"direction": "outbound", "call_id": call_id, "notes": notes}
                ),
                wait_until_answered=True,
                krisp_enabled=True,
                max_call_duration=Duration(seconds=settings.max_call_duration_seconds),
            )
        )
        await session_started
        participant = await ctx.wait_for_participant(identity=phone_number)
        pipeline_logger.mark_caller_joined(participant)
        twilio_call_sid = participant.attributes.get("sip.twilio.callSid")
        repository.mark_call_active(
            call_id=call_id,
            caller_number=phone_number,
            twilio_call_sid=twilio_call_sid,
        )
    except api.TwirpError as exc:
        message, sip_code = _sip_status(exc)
        logger.error("outbound SIP call failed: %s SIP %s", message, sip_code)
        repository.fail_call(call_id, message, sip_code)
        session_started.cancel()
        ctx.shutdown()
        return
    except Exception as exc:
        logger.exception("outbound call failed")
        repository.fail_call(call_id, str(exc))
        session_started.cancel()
        ctx.shutdown()
        return

    await session.generate_reply(
        instructions=(
            "You are calling from Lili Cantonese Kitchen about a table reservation. "
            "Greet the guest warmly as Mei, mention the restaurant name, and ask how you can help."
        )
    )


async def reservation_entrypoint(ctx: Any) -> None:
    require_provider_keys()
    metadata = _metadata_from_job(ctx)
    if metadata.get("direction") == "outbound":
        await start_outbound_session(ctx, metadata)
        return
    await start_inbound_session(ctx, metadata)


if LIVEKIT_IMPORT_ERROR is None:
    server = AgentServer()
    server.setup_fnc = prewarm
    server.rtc_session(
        agent_name=AGENT_NAME,
        on_session_end=on_session_end,
    )(reservation_entrypoint)
else:
    server = None


def build_server():
    if LIVEKIT_IMPORT_ERROR is not None:
        raise RuntimeError(
            "LiveKit dependencies are not available. Run `uv sync` before starting the agent."
        ) from LIVEKIT_IMPORT_ERROR
    return server


if __name__ == "__main__":
    if agents is None:
        raise RuntimeError(
            "LiveKit dependencies are not available. Run `uv sync` before starting the agent."
        ) from LIVEKIT_IMPORT_ERROR
    agents.cli.run_app(build_server())
