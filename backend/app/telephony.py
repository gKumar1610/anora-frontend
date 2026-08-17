from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from app import repository
from app.config import settings


E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
INDIA_E164_RE = re.compile(r"^\+91[1-9]\d{9}$")


class TelephonyConfigurationError(RuntimeError):
    pass


class PhoneNumberValidationError(ValueError):
    pass


@dataclass(frozen=True)
class OutboundCallRequest:
    phone_number: str
    guest_name: str | None = None
    notes: str | None = None


def normalize_phone_number(phone_number: str) -> str:
    compact = re.sub(r"[\s().-]", "", phone_number.strip())
    if compact.startswith("00"):
        compact = "+" + compact[2:]
    return compact


def validate_outbound_phone_number(phone_number: str, allowed_country: str | None = None) -> str:
    normalized = normalize_phone_number(phone_number)
    if not E164_RE.match(normalized):
        raise PhoneNumberValidationError("Phone number must be in E.164 format, for example +919876543210.")

    country = (allowed_country or settings.outbound_allowed_country).upper()
    if country == "IN" and not INDIA_E164_RE.match(normalized):
        raise PhoneNumberValidationError("Outbound calls are currently restricted to India E.164 numbers.")
    return normalized


def require_outbound_configuration() -> None:
    missing = []
    if not settings.has_livekit_credentials:
        missing.append("LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET")
    if not settings.sip_outbound_trunk_id:
        missing.append("SIP_OUTBOUND_TRUNK_ID")
    if not settings.sip_outbound_from_number:
        missing.append("SIP_OUTBOUND_FROM_NUMBER")
    if missing:
        raise TelephonyConfigurationError(
            "Missing outbound telephony configuration: " + "; ".join(missing)
        )


def outbound_metadata(
    call_id: str,
    phone_number: str,
    from_number: str,
    guest_name: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        "direction": "outbound",
        "call_id": call_id,
        "phone_number": phone_number,
        "from_number": from_number,
        "purpose": "reservation",
        "guest_name": guest_name or "",
        "notes": notes or "",
    }


async def create_outbound_call(
    request: OutboundCallRequest,
    livekit_api_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    phone_number = validate_outbound_phone_number(request.phone_number)
    require_outbound_configuration()
    from_number = normalize_phone_number(settings.sip_outbound_from_number)
    call_id = f"outbound-{uuid.uuid4().hex[:12]}"
    room_name = f"call-outbound-{uuid.uuid4().hex[:10]}"
    metadata = outbound_metadata(
        call_id=call_id,
        phone_number=phone_number,
        from_number=from_number,
        guest_name=request.guest_name,
        notes=request.notes,
    )
    call = repository.start_call(
        call_id=call_id,
        room_name=room_name,
        caller_number=phone_number,
        direction="outbound",
        from_number=from_number,
        to_number=phone_number,
        status="dialing",
    )

    try:
        from livekit import api
    except Exception as exc:  # pragma: no cover - depends on optional runtime package
        repository.fail_call(call_id, f"livekit-api is not installed: {exc}")
        raise TelephonyConfigurationError(f"livekit-api is not installed: {exc}") from exc

    lkapi = livekit_api_factory() if livekit_api_factory else api.LiveKitAPI()
    try:
        try:
            await lkapi.room.create_room(api.CreateRoomRequest(name=room_name))
        except api.TwirpError as exc:
            if "already" not in (getattr(exc, "message", "") or "").lower():
                raise
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=settings.agent_name,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
    except Exception as exc:
        sip_code = getattr(exc, "metadata", {}).get("sip_status_code") if hasattr(exc, "metadata") else None
        message = getattr(exc, "message", None) or str(exc)
        repository.fail_call(call_id, message, sip_code)
        raise
    finally:
        aclose: Callable[[], Awaitable[None]] | None = getattr(lkapi, "aclose", None)
        if aclose:
            await aclose()

    return call
