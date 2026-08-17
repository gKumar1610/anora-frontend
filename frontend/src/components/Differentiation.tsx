import Reveal from './Reveal';

export default function Differentiation() {
  return (
    <section className="section" id="why">
      <div className="wrap">
        <Reveal className="section-head">
          <div className="eyebrow">Why this works</div>
          <h2>A booking widget starts at the booking. We start at the call.</h2>
          <p className="note">
            A system that only records a reservation misses the guest who called and got nothing — no
            availability, no answer, no record. That's demand nobody else can see.
          </p>
        </Reveal>

        <Reveal className="compare">
          <div className="compare-col">
            <h4>Typical booking system</h4>
            <div className="compare-step">
              <span className="mark">01</span>
              <span>Guest calls during service</span>
            </div>
            <div className="compare-step">
              <span className="mark">02</span>
              <span>Someone free to answer? Sometimes.</span>
            </div>
            <div className="compare-step dim">
              <span className="mark">03</span>
              <span>No — call rings out, no record exists</span>
            </div>
            <div className="compare-step">
              <span className="mark">04</span>
              <span>Yes — booking recorded in their system</span>
            </div>
          </div>
          <div className="compare-col win">
            <h4>Arlong</h4>
            <div className="compare-step">
              <span className="mark">01</span>
              <span>Guest calls during service</span>
            </div>
            <div className="compare-step strong">
              <span className="mark">02</span>
              <span>Nami Voice always answers</span>
            </div>
            <div className="compare-step strong">
              <span className="mark">03</span>
              <span>Books the table — or captures the failed attempt as a demand signal</span>
            </div>
            <div className="compare-step strong">
              <span className="mark">04</span>
              <span>Either way, it's on your dashboard</span>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
