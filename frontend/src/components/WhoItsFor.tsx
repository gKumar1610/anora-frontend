import Reveal from './Reveal';

const SEGMENTS = [
  {
    name: 'Full-service restaurants',
    tag: '40–150 COVERS',
    body: 'Highest call volume, and every missed one is a measurable loss. The phone rings through service and nobody can answer — this is the pain felt first.',
  },
  {
    name: 'Cafés',
    tag: 'ENQUIRY-FIRST',
    body: 'Thin staffing makes the phone a real burden, even for questions like "are you open?" or "can I bring a dog?" Many take few or no bookings — Voice earns its keep on enquiries alone.',
  },
  {
    name: 'Bars & lounges',
    tag: 'WEEKEND PEAKS',
    body: 'High-volume phone enquiries and booth reservations with strong weekend peaks — a natural fit for Voice and, later, Reserve.',
  },
];

const WHY_SWITCH = [
  { n: '01', label: 'Recovering missed calls', body: '— direct, quantifiable revenue.' },
  { n: '02', label: 'Reducing commission', body: '— direct bookings instead of aggregator-mediated ones.' },
  { n: '03', label: 'Freeing staff attention', body: '— one less thing pulling servers off the floor.' },
  { n: '04', label: 'Visibility', body: "— knowing how the business is doing while there's still time to act." },
  { n: '05', label: 'Fewer errors', body: '— no double-bookings, no lost reservations.' },
];

export default function WhoItsFor() {
  return (
    <section className="section" id="who">
      <div className="wrap">
        <Reveal className="section-head">
          <div className="eyebrow">Built for the independent operator</div>
          <h2>For venues where the owner still picks up the phone.</h2>
        </Reveal>

        <Reveal className="who-grid">
          <div className="segments">
            {SEGMENTS.map((s) => (
              <div className="segment" key={s.name}>
                <div className="segment-head">
                  <h3>{s.name}</h3>
                  <span className="covers mono">{s.tag}</span>
                </div>
                <p>{s.body}</p>
              </div>
            ))}
          </div>

          <div className="why-switch">
            <div className="eyebrow label">Why venues switch</div>
            <ol>
              {WHY_SWITCH.map((w) => (
                <li key={w.n}>
                  <span className="n">{w.n}</span>
                  <span>
                    <strong>{w.label}</strong> {w.body}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
