import Reveal from './Reveal';

const MODULES = [
  {
    id: 'voice',
    idx: '01',
    name: 'Arlong Voice',
    tagline: 'Answers the phone.',
    desc: "Answers every inbound call, books the table, and handles guest enquiries — hours, seating, policy — strictly from your venue's own profile. Escalates and hands off to staff when it should. Live today, taking real reservations.",
    tag: 'LIVE',
    live: true,
  },
  {
    id: 'dashboard',
    idx: '02',
    name: 'Arlong Dashboard',
    tagline: 'Shows you everything, live.',
    desc: "Live calls with running transcripts, take-over of any call in progress, today's bookings, and full configuration of the agent and venue profile — in one screen. The business-analytics layer is what's being built next.",
    tag: 'LIVE · EXPANDING',
    live: true,
  },
  {
    id: 'reserve',
    idx: '03',
    name: 'Arlong Reserve',
    tagline: 'Takes bookings without a phone.',
    desc: 'A booking-enabled web presence that reads and writes the same availability Voice already checks — so phone and web can never double-book each other. Direct reservations, no aggregator commission.',
    tag: 'IN DEVELOPMENT',
    live: false,
  },
  {
    id: 'tables',
    idx: '04',
    name: 'Arlong Tables',
    tagline: 'Runs the floor.',
    desc: 'Floor plan, live table state, order capture, and itemised billing — so the agent on the phone knows which tables are genuinely free, not just how many slots are left.',
    tag: 'IN DEVELOPMENT',
    live: false,
  },
];

export default function Modules() {
  return (
    <section className="section" id="modules">
      <div className="wrap">
        <Reveal className="section-head">
          <div className="eyebrow">One venue, four touchpoints</div>
          <h2>Every module makes the others better.</h2>
          <p className="note">
            Booking, service, and billing become one continuous record per guest — instead of three
            systems reconciled after the fact.
          </p>
        </Reveal>

        <Reveal className="modules">
          {MODULES.map((m) => (
            <div className="module-row" id={m.id} key={m.id}>
              <div className="module-idx">{m.idx}</div>
              <div className="module-body">
                <h3>{m.name}</h3>
                <div className="module-tagline">{m.tagline}</div>
                <p className="desc">{m.desc}</p>
              </div>
              <div className={`module-tag ${m.live ? 'live' : ''}`.trim()}>{m.tag}</div>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
