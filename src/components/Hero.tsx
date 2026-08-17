import { useEffect, useState } from 'react';
import LiveCallButton from './LiveCallButton';

const TRANSCRIPT = [
  {
    who: 'NAMI VOICE',
    role: 'agent',
    text: "Good evening, Arlong's Kitchen — how can I help?",
  },
  {
    who: 'GUEST',
    role: 'guest',
    text: 'Hi, table for four this Saturday around eight?',
  },
  {
    who: 'NAMI VOICE',
    role: 'agent',
    text: 'Checking Saturday... 8:15pm is open. Shall I book that for you?',
  },
  {
    who: 'GUEST',
    role: 'guest',
    text: 'Perfect, thank you.',
  },
];

const BASE_DELAY = 1500;
const LINE_INTERVAL = 850;

export default function Hero() {
  const [visibleLines, setVisibleLines] = useState(0);
  const [stampVisible, setStampVisible] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisibleLines(TRANSCRIPT.length);
      setStampVisible(true);
      return;
    }

    const timers: number[] = TRANSCRIPT.map((_, i) =>
      window.setTimeout(() => setVisibleLines((v) => Math.max(v, i + 1)), BASE_DELAY + i * LINE_INTERVAL),
    );
    timers.push(
      window.setTimeout(
        () => setStampVisible(true),
        BASE_DELAY + TRANSCRIPT.length * LINE_INTERVAL + 300,
      ),
    );

    return () => timers.forEach((t) => window.clearTimeout(t));
  }, []);

  return (
    <section className="hero" id="hero">
      <div className="hero-grid">
        <div>
          <div className="eyebrow hero-eyebrow">Front-of-house operations</div>
          <h1>
            <span className="line">
              <span>Every unanswered call</span>
            </span>
            <span className="line">
              <span>
                is an empty <em>table</em> tonight.
              </span>
            </span>
          </h1>
          <p className="lede">
            Nami Voice answers your restaurant's phone the way your best host would — every ring, every
            service, including the ones you can't staff. It books the table, answers the guest's question,
            and hands off to your team the moment a person should take over.
          </p>
          <div className="hero-ctas">
            <LiveCallButton className="cta cta-primary">Request a Live Call</LiveCallButton>
            <a className="cta-text" href="#how-it-works">
              See how a call flows ↓
            </a>
          </div>
          <div className="hero-chips">
            <div className="chip">No ring goes unanswered</div>
            <div className="chip">Books against real availability</div>
            <div className="chip">Hands off to a person, on cue</div>
          </div>
        </div>

        <div className="call-card">
          <div className="call-head">
            <div className="call-head-left">
              <span className="live-dot" />
              <span className="label">LIVE&nbsp;·&nbsp;NAMI VOICE</span>
            </div>
            <div className="waveform" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
          <div className="call-venue">Arlong's Kitchen</div>
          <div className="call-sub mono">Inbound call · caller +91 98••• ••214</div>
          <div className="transcript">
            {TRANSCRIPT.map((line, i) => (
              <div key={i} className={`bubble ${line.role} ${i < visibleLines ? 'in-view' : ''}`.trim()}>
                <span className="who">{line.who}</span>
                {line.text}
              </div>
            ))}
          </div>
          <div className={`call-stamp ${stampVisible ? 'in-view' : ''}`.trim()}>
            <span className="status">BOOKED · TABLE FOR 4 · SAT 20:15</span>
            <span className="code">CONFIRMATION #LK-4471</span>
          </div>
        </div>
      </div>
    </section>
  );
}
