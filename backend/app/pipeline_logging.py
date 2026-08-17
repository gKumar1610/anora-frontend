from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable

from app import repository


PIPELINE_LOGGER_NAME = "restaurant-agent.pipeline"
logger = logging.getLogger(PIPELINE_LOGGER_NAME)
logger.setLevel(logging.INFO)


def _install_console_handler() -> None:
    """Give the pipeline logger its own stdout handler.

    Without this the timing/transcript lines are emitted at INFO but the root
    logger in app.agent is configured at WARNING, so they never reach the
    console. We attach a dedicated INFO handler so the latency logs always
    print regardless of the root level.

    Propagation is disabled: the LiveKit dev CLI installs its own INFO/DEBUG
    handler on ancestor loggers, so with propagation on each of our lines was
    re-emitted by that handler too (the duplicated/triplicated console output).
    Turning propagation off means our handler is the single emitter. Tests that
    rely on caplog attach their own capture handler directly to this logger
    (see tests/conftest-style autouse fixture), so capture still works.
    """
    if getattr(logger, "_pipeline_handler_installed", False):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d  %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.propagate = False
    logger._pipeline_handler_installed = True  # type: ignore[attr-defined]


# Opt out with PIPELINE_LOG_CONSOLE=0 (e.g. when a parent process configures logging).
if os.getenv("PIPELINE_LOG_CONSOLE", "1") != "0":
    _install_console_handler()


def _seconds_to_ms(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value) * 1000, 3)
    except (TypeError, ValueError):
        return None


def _number(value: Any, precision: int = 3) -> float | int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric.is_integer():
        return int(numeric)
    return round(numeric, precision)


def _epoch_seconds(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.timestamp()
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iso_from_epoch(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def _clean(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in fields.items()
        if value is not None and value != "" and value != {}
    }


def _format_ms(value: Any) -> str | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric >= 1000:
        return f"{numeric / 1000:.2f}s"
    if numeric.is_integer():
        return f"{int(numeric)}ms"
    return f"{numeric:.1f}ms"


def _format_timing(parts: list[tuple[str, Any]]) -> str:
    rendered = []
    for label, value in parts:
        formatted = _format_ms(value)
        if formatted is not None:
            rendered.append(f"{label} {formatted}")
    return " | ".join(rendered)


def log_pipeline_event(event_name: str, fields: dict[str, Any]) -> None:
    message = format_console_event(event_name, fields)
    if message:
        logger.info(message)


def log_transcript_event(speaker: str, text: str) -> None:
    label = "Caller" if speaker == "caller" else "Agent"
    logger.info("TRANSCRIPT  %-6s %s", f"{label}:", text.strip())


def format_console_event(event_name: str, fields: dict[str, Any]) -> str | None:
    fields = _clean(fields)

    if event_name == "voice_pipeline.stt":
        timing = _format_timing(
            [
                ("duration", fields.get("duration_ms")),
                ("audio", fields.get("audio_duration_ms")),
                ("queue", fields.get("acquire_time_ms")),
            ]
        )
        return f"TIMING      STT    {timing}" if timing else None

    if event_name == "voice_pipeline.llm":
        timing = _format_timing(
            [
                ("duration", fields.get("duration_ms")),
                ("first_token", fields.get("ttft_ms")),
            ]
        )
        return f"TIMING      LLM    {timing}" if timing else None

    if event_name == "voice_pipeline.tts":
        timing = _format_timing(
            [
                ("duration", fields.get("duration_ms")),
                ("first_audio", fields.get("ttfb_ms")),
                ("audio", fields.get("audio_duration_ms")),
                ("queue", fields.get("acquire_time_ms")),
            ]
        )
        return f"TIMING      TTS    {timing}" if timing else None

    if event_name == "voice_pipeline.user_turn":
        timing = _format_timing(
            [
                ("speech", fields.get("speech_duration_ms")),
                ("transcription", fields.get("transcription_delay_ms")),
                ("end_of_turn", fields.get("end_of_turn_delay_ms")),
                ("turn_callback", fields.get("on_user_turn_completed_delay_ms")),
            ]
        )
        return f"TIMING      USER   {timing}" if timing else None

    if event_name == "voice_pipeline.assistant_turn":
        timing = _format_timing(
            [
                ("end_to_end", fields.get("e2e_latency_ms")),
                ("llm_first_token", fields.get("llm_node_ttft_ms")),
                ("tts_first_audio", fields.get("tts_node_ttfb_ms")),
                ("playback", fields.get("playback_latency_ms")),
            ]
        )
        return f"TIMING      AGENT  {timing}" if timing else None

    return None


def format_model_metric(event_context: dict[str, Any], metrics: Any) -> tuple[str, dict[str, Any]] | None:
    metric_type = getattr(metrics, "type", "") or metrics.__class__.__name__.lower()
    base = {
        "label": getattr(metrics, "label", None),
    }

    if metric_type in {"stt_metrics", "sttmetrics"}:
        return (
            "voice_pipeline.stt",
            _clean(
                base
                | {
                    "component": "stt",
                    "duration_ms": _seconds_to_ms(getattr(metrics, "duration", None)),
                    "audio_duration_ms": _seconds_to_ms(
                        getattr(metrics, "audio_duration", None)
                    ),
                    "acquire_time_ms": _seconds_to_ms(getattr(metrics, "acquire_time", None)),
                }
            ),
        )

    if metric_type in {"llm_metrics", "llmmetrics"}:
        return (
            "voice_pipeline.llm",
            _clean(
                base
                | {
                    "component": "llm",
                    "duration_ms": _seconds_to_ms(getattr(metrics, "duration", None)),
                    "ttft_ms": _seconds_to_ms(getattr(metrics, "ttft", None)),
                }
            ),
        )

    if metric_type in {"tts_metrics", "ttsmetrics"}:
        return (
            "voice_pipeline.tts",
            _clean(
                base
                | {
                    "component": "tts",
                    "duration_ms": _seconds_to_ms(getattr(metrics, "duration", None)),
                    "ttfb_ms": _seconds_to_ms(getattr(metrics, "ttfb", None)),
                    "audio_duration_ms": _seconds_to_ms(
                        getattr(metrics, "audio_duration", None)
                    ),
                    "acquire_time_ms": _seconds_to_ms(getattr(metrics, "acquire_time", None)),
                }
            ),
        )

    return None


def format_turn_metric(event_context: dict[str, Any], item: Any) -> tuple[str, dict[str, Any]] | None:
    role = getattr(item, "role", None)
    metrics = getattr(item, "metrics", None) or {}
    if not isinstance(metrics, dict):
        return None

    started_at = _number(metrics.get("started_speaking_at"), 6)
    stopped_at = _number(metrics.get("stopped_speaking_at"), 6)
    speech_duration_ms = None
    if started_at is not None and stopped_at is not None:
        speech_duration_ms = _seconds_to_ms(float(stopped_at) - float(started_at))

    base = {
        "role": role,
        "speech_duration_ms": speech_duration_ms,
    }

    if role == "user":
        fields = _clean(
            base
            | {
                "transcription_delay_ms": _seconds_to_ms(
                    metrics.get("transcription_delay")
                ),
                "end_of_turn_delay_ms": _seconds_to_ms(metrics.get("end_of_turn_delay")),
                "on_user_turn_completed_delay_ms": _seconds_to_ms(
                    metrics.get("on_user_turn_completed_delay")
                ),
            }
        )
        if len(fields) > len(_clean(base)):
            return "voice_pipeline.user_turn", fields
        return None

    if role == "assistant":
        fields = _clean(
            base
            | {
                "llm_node_ttft_ms": _seconds_to_ms(metrics.get("llm_node_ttft")),
                "tts_node_ttfb_ms": _seconds_to_ms(metrics.get("tts_node_ttfb")),
                "playback_latency_ms": _seconds_to_ms(metrics.get("playback_latency")),
                "e2e_latency_ms": _seconds_to_ms(metrics.get("e2e_latency")),
            }
        )
        if len(fields) > len(_clean(base)):
            return "voice_pipeline.assistant_turn", fields
    return None


def _bar(value_ms: Any, scale_ms: float, width: int = 20) -> str:
    numeric = _number(value_ms)
    if not isinstance(numeric, (int, float)) or numeric <= 0:
        return ""
    filled = int(min(width, max(1, round((float(numeric) / scale_ms) * width))))
    return "#" * filled + "-" * (width - filled)


class TurnLatencyTracker:
    """Aggregates STT/LLM/TTS/turn metrics into one per-turn console block.

    The individual metric events fire at different moments and out of order.
    This buffers them per turn and, once the assistant turn (which carries the
    end-to-end latency) lands, prints a single aligned block that makes the slow
    stage obvious.
    """

    # Stages contributing to caller-perceived response latency and a rough
    # budget (ms) used only to scale the ASCII bars.
    _STAGE_BUDGET = {
        "stt": 800,
        "llm": 1500,
        "tts": 800,
    }

    def __init__(self, call_id: str) -> None:
        self.call_id = call_id
        self._turn = 0
        self._pending: dict[str, Any] = {}

    @property
    def _short_call(self) -> str:
        return self.call_id[:8]

    def record(self, event_name: str, fields: dict[str, Any]) -> None:
        if event_name == "voice_pipeline.stt":
            self._pending["stt_ms"] = fields.get("duration_ms")
            self._pending["stt_audio_ms"] = fields.get("audio_duration_ms")
        elif event_name == "voice_pipeline.llm":
            self._pending["llm_ms"] = fields.get("duration_ms")
            self._pending["llm_ttft_ms"] = fields.get("ttft_ms")
        elif event_name == "voice_pipeline.tts":
            self._pending["tts_ms"] = fields.get("duration_ms")
            self._pending["tts_ttfb_ms"] = fields.get("ttfb_ms")
        elif event_name == "voice_pipeline.user_turn":
            self._pending["user_speech_ms"] = fields.get("speech_duration_ms")
            self._pending["eou_ms"] = fields.get("end_of_turn_delay_ms")
        elif event_name == "voice_pipeline.assistant_turn":
            # The assistant turn closes the loop; flush the aggregated block.
            self._pending["e2e_ms"] = fields.get("e2e_latency_ms")
            self._pending["llm_ttft_ms"] = (
                fields.get("llm_node_ttft_ms") or self._pending.get("llm_ttft_ms")
            )
            self._pending["tts_ttfb_ms"] = (
                fields.get("tts_node_ttfb_ms") or self._pending.get("tts_ttfb_ms")
            )
            self._pending["playback_ms"] = fields.get("playback_latency_ms")
            self._flush()

    def _bottleneck(self) -> str | None:
        candidates = {
            stage: _number(self._pending.get(f"{stage}_ms"))
            for stage in ("stt", "llm", "tts")
        }
        candidates = {
            stage: value
            for stage, value in candidates.items()
            if isinstance(value, (int, float))
        }
        if not candidates:
            return None
        slowest = max(candidates, key=candidates.get)
        # Only flag a stage when it clearly dominates the response time, so the
        # marker means "look here" rather than just "technically the largest".
        if candidates[slowest] < 700:
            return None
        others = [v for stage, v in candidates.items() if stage != slowest]
        if others and candidates[slowest] < 1.5 * max(others):
            return None
        return slowest

    def _flush(self) -> None:
        self._turn += 1
        p = self._pending
        bottleneck = self._bottleneck()

        lines = [
            f"=== call {self._short_call}  turn {self._turn} "
            f"{'=' * 28}"
        ]

        def stage_line(stage: str, primary_label: str, primary_key: str, secondary: str) -> None:
            duration = p.get(f"{stage}_ms")
            if duration is None and p.get(primary_key) is None:
                return
            marker = "  <- SLOWEST" if stage == bottleneck else ""
            bar = _bar(duration, self._STAGE_BUDGET[stage])
            head = _format_ms(duration) or "-"
            extra = _format_ms(p.get(primary_key))
            extra_str = f"  {primary_label} {extra}" if extra else ""
            lines.append(
                f"  {stage.upper():<4} {head:>8}  {bar}{extra_str}{marker}"
            )

        stage_line("stt", "audio", "stt_audio_ms", "")
        stage_line("llm", "ttft", "llm_ttft_ms", "")
        stage_line("tts", "ttfb", "tts_ttfb_ms", "")

        e2e = _format_ms(p.get("e2e_ms"))
        if e2e:
            eou = _format_ms(p.get("eou_ms"))
            eou_str = f"  (end-of-turn detect {eou})" if eou else ""
            lines.append(f"  {'-' * 44}")
            lines.append(f"  E2E  {e2e:>8}  caller-stopped -> agent-audio{eou_str}")

        logger.info("\n".join(lines))
        self._pending = {}


class VoicePipelineLogger:
    def __init__(self, call_id: str, room_name: str, direction: str = "inbound") -> None:
        self.call_id = call_id
        self.room_name = room_name
        self.direction = direction
        self.session_started_monotonic = time.monotonic()
        self.caller_joined_wall: float | None = None
        self.caller_left_wall: float | None = None
        self.turn_tracker = TurnLatencyTracker(call_id)

    @property
    def context(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "room_name": self.room_name,
            "direction": self.direction,
        }

    def attach_model_plugins(self, *plugins: Any) -> None:
        for plugin in plugins:
            on = getattr(plugin, "on", None)
            if not callable(on):
                continue

            def record_metric(metrics: Any, plugin_context: dict[str, Any] = self.context) -> None:
                formatted = format_model_metric(plugin_context, metrics)
                if not formatted:
                    return
                event_name, fields = formatted
                log_pipeline_event(event_name, fields)
                self.turn_tracker.record(event_name, fields)

            on("metrics_collected", record_metric)

    def attach_session(self, session: Any) -> None:
        on = getattr(session, "on", None)
        if not callable(on):
            return
        on("conversation_item_added", self.log_conversation_item)
        on("user_state_changed", self.log_user_state_changed)
        on("agent_state_changed", self.log_agent_state_changed)

    def attach_room(
        self,
        room: Any,
        *,
        is_caller_participant: Callable[[Any], bool],
    ) -> None:
        on = getattr(room, "on", None)
        if not callable(on):
            return

        def participant_connected(participant: Any) -> None:
            if is_caller_participant(participant):
                self.mark_caller_joined(participant)

        def participant_disconnected(participant: Any) -> None:
            if is_caller_participant(participant):
                self.mark_caller_left(participant)

        on("participant_connected", participant_connected)
        on("participant_disconnected", participant_disconnected)

    def register_shutdown(self, ctx: Any) -> None:
        add_shutdown_callback = getattr(ctx, "add_shutdown_callback", None)
        if not callable(add_shutdown_callback):
            return

        async def on_shutdown(*_: Any) -> None:
            self.complete_call()

        add_shutdown_callback(on_shutdown)

    def log_conversation_item(self, event: Any) -> None:
        item = getattr(event, "item", None)
        formatted = format_turn_metric(self.context, item)
        if formatted:
            event_name, fields = formatted
            log_pipeline_event(event_name, fields)
            self.turn_tracker.record(event_name, fields)

    def log_user_state_changed(self, event: Any) -> None:
        pass

    def log_agent_state_changed(self, event: Any) -> None:
        pass

    def mark_caller_joined(self, participant: Any) -> None:
        if self.caller_joined_wall is not None:
            return
        joined_wall = _epoch_seconds(getattr(participant, "joined_at", None)) or time.time()
        self.caller_joined_wall = joined_wall
        repository.mark_caller_joined(self.call_id, _iso_from_epoch(joined_wall))

    def mark_caller_left(self, participant: Any | None = None) -> None:
        if self.caller_joined_wall is None or self.caller_left_wall is not None:
            return
        left_wall = time.time()
        self.caller_left_wall = left_wall
        duration_seconds = max(0.0, left_wall - self.caller_joined_wall)
        repository.mark_caller_left(
            self.call_id,
            _iso_from_epoch(left_wall),
            int(round(duration_seconds)),
        )

    def complete_call(self) -> None:
        if self.caller_joined_wall is not None and self.caller_left_wall is None:
            self.mark_caller_left()
