import { DEMO_MAILTO } from '../constants';

export default function FinalCta() {
  return (
    <section className="final-cta">
      <div className="eyebrow">Ready when your phone isn't</div>
      <h2>Let's find out how many calls you're missing.</h2>
      <p className="note">
        Setup is measured in hours, not weeks, and nothing you already use has to be replaced to start.
      </p>
      <div className="hero-ctas">
        <a className="cta cta-primary" href={DEMO_MAILTO}>
          Request a Live Call
        </a>
      </div>
    </section>
  );
}
