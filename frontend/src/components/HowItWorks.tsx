import type { CSSProperties } from 'react';
import Reveal from './Reveal';

const STEPS = [
  {
    idx: '01 · GREETS',
    title: "In your venue's voice",
    body: 'The greeting, tone, and persona are set by you, not a script — and change instantly, with no redeployment.',
  },
  {
    idx: '02 · LISTENS',
    title: 'Collects the details',
    body: "Name, date, time, party size. If anything's unclear, it asks again naturally — a wrong booking is worse than a slow one.",
  },
  {
    idx: '03 · CHECKS',
    title: 'Real availability',
    body: 'Against your actual capacity and booking rules, live — not a guess, and not a static allocation.',
  },
  {
    idx: '04 · CONFIRMS',
    title: 'Books, and reads it back',
    body: 'The table is booked and a confirmation code is read back out loud, before the call ends.',
  },
];

export default function HowItWorks() {
  return (
    <section className="section" id="how-it-works">
      <div className="wrap">
        <Reveal className="section-head">
          <div className="eyebrow">How a call actually flows</div>
          <h2>Answered the way your best host would answer it.</h2>
        </Reveal>

        <Reveal className="flow reveal-stagger">
          {STEPS.map((step, i) => (
            <div className="flow-step" style={{ '--i': i } as CSSProperties} key={step.idx}>
              <div className="idx">{step.idx}</div>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </div>
          ))}
        </Reveal>

        <Reveal className="callout">
          <p>
            Anything outside its scope — a large party, an unusual request — gets routed rather than
            fumbled. Staff can take over a live call from the dashboard, mid-conversation, without the
            guest noticing a seam.
          </p>
          <p className="quote">
            Not an IVR.
            <br />
            Not a script.
            <br />
            A person, one tap away.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
