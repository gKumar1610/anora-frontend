from __future__ import annotations

import json

from app.db import connect, init_db
from app.defaults import DEFAULT_RESTAURANT_PROFILE, DEFAULT_SYSTEM_PROMPT
from app import repository


def main() -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM transcript_events")
        conn.execute("DELETE FROM bookings")
        conn.execute("DELETE FROM calls")
        conn.commit()

    repository.set_setting("system_prompt", DEFAULT_SYSTEM_PROMPT)
    repository.set_setting(
        "restaurant_profile", json.dumps(DEFAULT_RESTAURANT_PROFILE, indent=2)
    )

    live_call = repository.start_call(
        call_id="demo-live-001",
        room_name="call-lili-live",
        caller_number="+919876543210",
        twilio_call_sid="CA_DEMO_LIVE",
    )
    for speaker, text in [
        ("caller", "Hi, I would like to book a table for four tomorrow evening."),
        ("agent", "Of course. I can help with that. What time would you like to join us at Lili?"),
        ("caller", "Around seven thirty, if you have availability."),
        ("agent", "We do have availability at 7:30 PM tomorrow for four guests. May I have the booking name?"),
        ("caller", "Ananya Reddy. It is for a birthday dinner, so a quieter table would be great."),
        ("agent", "Thank you, Ananya. I have noted a quieter table for a birthday dinner. What is the best phone number for the reservation?"),
        ("caller", "You can use this number."),
        ("agent", "Perfect. Your table for four is confirmed for tomorrow at 7:30 PM."),
    ]:
        repository.add_transcript_event(live_call["id"], speaker, text)
    repository.create_booking(
        guest_name="Ananya Reddy",
        phone="+919876543210",
        party_size=4,
        reservation_date="2026-06-08",
        reservation_time="19:30",
        notes="Birthday dinner, prefers a quieter table",
        call_id=live_call["id"],
    )
    repository.end_call(live_call["id"])

    completed_call = repository.start_call(
        call_id="demo-call-002",
        room_name="call-lili-002",
        caller_number="+919845612340",
        twilio_call_sid="CA_DEMO_002",
    )
    for speaker, text in [
        ("caller", "Can I reserve a table for two tonight?"),
        ("agent", "Absolutely. What time would you prefer?"),
        ("caller", "Eight fifteen."),
        ("agent", "We have 8:15 PM available. May I have the guest name?"),
        ("caller", "Rahul Menon. It is our anniversary."),
        ("agent", "Your table for two is confirmed for 8:15 PM tonight. I have added the anniversary note."),
    ]:
        repository.add_transcript_event(completed_call["id"], speaker, text)
    repository.create_booking(
        guest_name="Rahul Menon",
        phone="+919845612340",
        party_size=2,
        reservation_date="2026-06-07",
        reservation_time="20:15",
        notes="Anniversary dinner",
        call_id=completed_call["id"],
    )
    repository.end_call(completed_call["id"])

    inquiry_call = repository.start_call(
        call_id="demo-call-003",
        room_name="call-lili-003",
        caller_number="+919700456789",
        twilio_call_sid="CA_DEMO_003",
    )
    for speaker, text in [
        ("caller", "Do you take reservations for twelve people?"),
        ("agent", "For parties over ten, I can collect your details and our team will call back to confirm."),
        ("caller", "That is okay. I will call back once I know the exact number."),
        ("agent", "Of course. We will be happy to help when you are ready."),
    ]:
        repository.add_transcript_event(inquiry_call["id"], speaker, text)
    repository.end_call(inquiry_call["id"])

    for guest_name, phone, party_size, date, time, notes in [
        ("Priya Shah", "+919901112233", 6, "2026-06-09", "21:00", "Vegetarian tasting recommendations requested"),
        ("Karan Malhotra", "+919633445566", 5, "2026-06-10", "19:00", "One high chair needed"),
        ("Meera Iyer", "+919811223344", 3, "2026-06-11", "18:45", "Prefers non-spicy options"),
    ]:
        repository.create_booking(
            guest_name=guest_name,
            phone=phone,
            party_size=party_size,
            reservation_date=date,
            reservation_time=time,
            notes=notes,
        )
    print("Seeded Lili Cantonese Kitchen demo data.")


if __name__ == "__main__":
    main()
