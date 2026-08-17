import type { CSSProperties } from 'react';
import Reveal from './Reveal';

const ITEMS = [
  {
    idx: '01',
    title: 'The phone goes unanswered',
    body: 'During a busy service nobody has a free hand. Every missed call is a party of four that booked somewhere else — and it leaves no trace, so you never know how many you lost.',
  },
  {
    idx: '02',
    title: 'Bookings arrive through too many doors',
    body: 'Phone, Instagram, WhatsApp, walk-ins, and aggregators all feed the same floor. Reconciling them by hand is how double-bookings happen.',
  },
  {
    idx: '03',
    title: "The floor lives in someone's head",
    body: 'Which table is seated, which is waiting on food, which needs clearing. When the person holding that state steps away, service slows down.',
  },
  {
    idx: '04',
    title: 'The owner finds out the next morning',
    body: "Numbers arrive too late and too coarse to act on. How many calls did we miss last Friday? There's usually no way to know.",
  },
];

export default function Problem() {
  return (
    <section className="section" id="problem">
      <div className="wrap">
        <Reveal className="section-head">
          <div className="eyebrow">What front of house runs on</div>
          <h2>Four things held together by memory, not systems.</h2>
          <p className="note">
            Each of these is survivable on its own — which is exactly why they persist. Together they cap
            how much a venue can earn from the covers it already has.
          </p>
        </Reveal>

        <Reveal className="problem-grid reveal-stagger">
          {ITEMS.map((item, i) => (
            <div className="problem-item" style={{ '--i': i } as CSSProperties} key={item.idx}>
              <div className="idx">{item.idx}</div>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
