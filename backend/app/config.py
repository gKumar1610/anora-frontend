from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(".env.local")
load_dotenv()

AGENT_NAME = "inbound-voice-agent"


@dataclass(frozen=True)
class Settings:
    livekit_url: str = os.getenv("LIVEKIT_URL", "")
    livekit_api_key: str = os.getenv("LIVEKIT_API_KEY", "")
    livekit_api_secret: str = os.getenv("LIVEKIT_API_SECRET", "")
    sip_outbound_trunk_id: str = os.getenv("SIP_OUTBOUND_TRUNK_ID", "")
    sip_outbound_from_number: str = os.getenv("SIP_OUTBOUND_FROM_NUMBER", "")
    outbound_allowed_country: str = os.getenv("OUTBOUND_ALLOWED_COUNTRY", "IN")
    max_call_duration_seconds: int = int(os.getenv("MAX_CALL_DURATION_SECONDS", "900"))
    database_path: str = os.getenv(
        "DATABASE_PATH", ".data/restaurant_voice_agent.sqlite3"
    )
    agent_name: str = AGENT_NAME
    public_app_url: str = os.getenv("PUBLIC_APP_URL", "http://localhost:8000")

    @property
    def has_livekit_credentials(self) -> bool:
        return bool(self.livekit_url and self.livekit_api_key and self.livekit_api_secret)

    @property
    def database_file(self) -> Path:
        return Path(self.database_path)


settings = Settings()
