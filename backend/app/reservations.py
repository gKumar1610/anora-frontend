from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app import repository


MAX_STANDARD_PARTY_SIZE = 10
MAX_BOOKINGS_PER_SLOT = 8


@dataclass(frozen=True)
class Availability:
    available: bool
    reason: str
    suggested_times: list[str]


def validate_reservation_request(
    party_size: int,
    reservation_date: str,
    reservation_time: str,
) -> None:
    if party_size < 1:
        raise ValueError("Party size must be at least 1.")
    if party_size > MAX_STANDARD_PARTY_SIZE:
        raise ValueError("Parties larger than 10 require a manual callback.")
    if not reservation_date:
        raise ValueError("A reservation date is required (YYYY-MM-DD).")
    if not reservation_time:
        raise ValueError("A reservation time is required (HH:MM).")
    try:
        datetime.strptime(reservation_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Reservation date {reservation_date!r} is not valid; expected YYYY-MM-DD."
        ) from None
    try:
        datetime.strptime(reservation_time, "%H:%M")
    except ValueError:
        raise ValueError(
            f"Reservation time {reservation_time!r} is not valid; expected 24-hour HH:MM."
        ) from None


def check_availability(
    party_size: int,
    reservation_date: str,
    reservation_time: str,
    db_path: str | None = None,
) -> Availability:
    validate_reservation_request(party_size, reservation_date, reservation_time)
    booked = repository.booking_count_for_slot(reservation_date, reservation_time, db_path)
    if booked < MAX_BOOKINGS_PER_SLOT:
        return Availability(True, "Tables are available for that slot.", [])
    return Availability(
        False,
        "That slot is fully booked.",
        suggested_times=_nearby_times(reservation_time),
    )


def create_confirmed_booking(
    guest_name: str,
    phone: str | None,
    party_size: int,
    reservation_date: str,
    reservation_time: str,
    notes: str | None = None,
    call_id: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    availability = check_availability(party_size, reservation_date, reservation_time, db_path)
    if not availability.available:
        raise ValueError(
            f"{availability.reason} Suggested times: {', '.join(availability.suggested_times)}"
        )
    return repository.create_booking(
        guest_name=guest_name,
        phone=phone,
        party_size=party_size,
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        notes=notes,
        call_id=call_id,
        db_path=db_path,
    )


def _nearby_times(reservation_time: str) -> list[str]:
    hour, minute = [int(part) for part in reservation_time.split(":")]
    candidates = []
    for delta in (-30, 30, 60):
        total = hour * 60 + minute + delta
        if 10 * 60 <= total <= 23 * 60:
            candidates.append(f"{total // 60:02d}:{total % 60:02d}")
    return candidates or ["19:00", "20:30"]

