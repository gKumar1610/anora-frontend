from __future__ import annotations

import json
import secrets
import string
from datetime import datetime, timezone
from typing import Any

from app.db import connect, init_db


ACTIVE_CALL_STATUSES = ("active", "dialing", "owner_active")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def get_setting(key: str, default: str = "", db_path: str | None = None) -> str:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str, db_path: str | None = None) -> dict[str, Any]:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO settings(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, timestamp),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM settings WHERE key = ?", (key,)).fetchone()
        return row_to_dict(row)


def get_restaurant_profile(db_path: str | None = None) -> dict[str, Any]:
    raw = get_setting("restaurant_profile", "{}", db_path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def start_call(
    call_id: str,
    room_name: str,
    caller_number: str | None = None,
    twilio_call_sid: str | None = None,
    direction: str = "inbound",
    from_number: str | None = None,
    to_number: str | None = None,
    status: str = "active",
    db_path: str | None = None,
) -> dict[str, Any]:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO calls(
              id, room_name, direction, caller_number, from_number, to_number,
              twilio_call_sid, status, started_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              status = excluded.status,
              direction = excluded.direction,
              caller_number = COALESCE(excluded.caller_number, calls.caller_number),
              from_number = COALESCE(excluded.from_number, calls.from_number),
              to_number = COALESCE(excluded.to_number, calls.to_number),
              twilio_call_sid = COALESCE(excluded.twilio_call_sid, calls.twilio_call_sid),
              failure_reason = NULL,
              sip_status_code = NULL,
              updated_at = excluded.updated_at
            """,
            (
                call_id,
                room_name,
                direction,
                caller_number,
                from_number,
                to_number,
                twilio_call_sid,
                status,
                timestamp,
                timestamp,
            ),
        )
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone())


def get_call(call_id: str, db_path: str | None = None) -> dict[str, Any]:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        return row_to_dict(row)


def mark_call_active(
    call_id: str,
    caller_number: str | None = None,
    twilio_call_sid: str | None = None,
    db_path: str | None = None,
) -> None:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET status = 'active',
                caller_number = COALESCE(?, caller_number),
                twilio_call_sid = COALESCE(?, twilio_call_sid),
                failure_reason = NULL,
                sip_status_code = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (caller_number, twilio_call_sid, timestamp, call_id),
        )
        conn.commit()


def mark_owner_joined(
    call_id: str,
    owner_identity: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET status = 'owner_active',
                owner_identity = ?,
                owner_joined_at = COALESCE(owner_joined_at, ?),
                handoff_status = 'owner_active',
                updated_at = ?
            WHERE id = ?
            """,
            (owner_identity, timestamp, timestamp, call_id),
        )
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone())


def mark_agent_removed(
    call_id: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET agent_left_at = COALESCE(agent_left_at, ?),
                handoff_status = 'owner_active',
                updated_at = ?
            WHERE id = ?
            """,
            (timestamp, timestamp, call_id),
        )
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone())


def is_owner_handoff_room(room_name: str, db_path: str | None = None) -> bool:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM calls
            WHERE room_name = ?
              AND status = 'owner_active'
              AND handoff_status = 'owner_active'
            LIMIT 1
            """,
            (room_name,),
        ).fetchone()
        return row is not None


def mark_caller_joined(
    call_id: str,
    caller_joined_at: str,
    db_path: str | None = None,
) -> None:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET caller_joined_at = COALESCE(caller_joined_at, ?),
                updated_at = ?
            WHERE id = ?
            """,
            (caller_joined_at, timestamp, call_id),
        )
        conn.commit()


def mark_caller_left(
    call_id: str,
    caller_left_at: str,
    caller_duration_seconds: int,
    db_path: str | None = None,
) -> None:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET caller_left_at = COALESCE(caller_left_at, ?),
                caller_duration_seconds = COALESCE(caller_duration_seconds, ?),
                status = CASE WHEN status = 'owner_active' THEN 'completed' ELSE status END,
                ended_at = CASE WHEN status = 'owner_active' THEN COALESCE(ended_at, ?) ELSE ended_at END,
                duration_seconds = CASE
                  WHEN status = 'owner_active'
                  THEN CAST((julianday(?) - julianday(started_at)) * 86400 AS INTEGER)
                  ELSE duration_seconds
                END,
                updated_at = ?
            WHERE id = ?
            """,
            (caller_left_at, caller_duration_seconds, caller_left_at, caller_left_at, timestamp, call_id),
        )
        conn.commit()


def fail_call(
    call_id: str,
    failure_reason: str,
    sip_status_code: str | None = None,
    db_path: str | None = None,
) -> None:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET status = 'failed',
                failure_reason = ?,
                sip_status_code = ?,
                ended_at = COALESCE(ended_at, ?),
                duration_seconds = CAST((julianday(?) - julianday(started_at)) * 86400 AS INTEGER),
                updated_at = ?
            WHERE id = ?
            """,
            (failure_reason, sip_status_code, timestamp, timestamp, timestamp, call_id),
        )
        conn.commit()


def end_call(call_id: str, db_path: str | None = None) -> None:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET status = 'completed',
                ended_at = ?,
                duration_seconds = CAST((julianday(?) - julianday(started_at)) * 86400 AS INTEGER),
                updated_at = ?
            WHERE id = ?
            """,
            (timestamp, timestamp, timestamp, call_id),
        )
        conn.commit()


def end_call_by_room(room_name: str, db_path: str | None = None) -> None:
    init_db(db_path)
    timestamp = now_iso()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE calls
            SET status = 'completed',
                ended_at = ?,
                duration_seconds = CAST((julianday(?) - julianday(started_at)) * 86400 AS INTEGER),
                updated_at = ?
            WHERE room_name = ?
              AND status IN ('active', 'dialing')
              AND COALESCE(handoff_status, '') != 'owner_active'
            """,
            (timestamp, timestamp, timestamp, room_name),
        )
        conn.commit()


def add_transcript_event(
    call_id: str,
    speaker: str,
    text: str,
    is_final: bool = True,
    db_path: str | None = None,
) -> dict[str, Any]:
    init_db(db_path)
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO transcript_events(call_id, speaker, text, is_final, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (call_id, speaker, text.strip(), int(is_final), now_iso()),
        )
        conn.commit()
        return row_to_dict(
            conn.execute("SELECT * FROM transcript_events WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )


def list_transcript(call_id: str, db_path: str | None = None) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM transcript_events
            WHERE call_id = ?
            ORDER BY id ASC
            """,
            (call_id,),
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def list_transcript_since(
    call_id: str,
    after_id: int = 0,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM transcript_events
            WHERE call_id = ? AND id > ?
            ORDER BY id ASC
            """,
            (call_id, after_id),
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def list_calls(limit: int = 20, db_path: str | None = None) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT c.*,
              (SELECT COUNT(*) FROM transcript_events t WHERE t.call_id = c.id) AS transcript_count,
              (SELECT COUNT(*) FROM bookings b WHERE b.call_id = c.id) AS booking_count
            FROM calls c
            ORDER BY c.started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def generate_confirmation_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "LILI-" + "".join(secrets.choice(alphabet) for _ in range(5))


def create_booking(
    guest_name: str,
    phone: str | None,
    party_size: int,
    reservation_date: str,
    reservation_time: str,
    notes: str | None = None,
    call_id: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    init_db(db_path)
    with connect(db_path) as conn:
        for _ in range(5):
            code = generate_confirmation_code()
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO bookings(
                      confirmation_code, guest_name, phone, party_size,
                      reservation_date, reservation_time, notes, call_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        code,
                        guest_name.strip(),
                        phone,
                        party_size,
                        reservation_date,
                        reservation_time,
                        notes,
                        call_id,
                        now_iso(),
                        now_iso(),
                    ),
                )
                conn.commit()
                return row_to_dict(
                    conn.execute("SELECT * FROM bookings WHERE id = ?", (cursor.lastrowid,)).fetchone()
                )
            except Exception:
                continue
        raise RuntimeError("Could not generate a unique confirmation code")


def list_bookings(limit: int = 50, db_path: str | None = None) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM bookings
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def booking_count_for_slot(
    reservation_date: str,
    reservation_time: str,
    db_path: str | None = None,
) -> int:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM bookings
            WHERE reservation_date = ? AND reservation_time = ? AND status = 'confirmed'
            """,
            (reservation_date, reservation_time),
        ).fetchone()
        return int(row["count"])


def get_metrics(db_path: str | None = None) -> dict[str, Any]:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM calls) AS total_calls,
              (SELECT COUNT(*) FROM calls WHERE status IN ('active', 'dialing', 'owner_active')) AS active_calls,
              (SELECT COUNT(*) FROM bookings WHERE status = 'confirmed') AS total_bookings,
              (
                SELECT COUNT(DISTINCT call_id)
                FROM bookings
                WHERE status = 'confirmed' AND call_id IS NOT NULL
              ) AS booked_calls,
              (SELECT COUNT(*) FROM transcript_events) AS transcript_events
            """
        ).fetchone()
    data = row_to_dict(row)
    total_calls = data.get("total_calls", 0) or 0
    booked_calls = data.pop("booked_calls", 0) or 0
    data["conversion_rate"] = round((booked_calls / total_calls) * 100, 1) if total_calls else 0
    return data
