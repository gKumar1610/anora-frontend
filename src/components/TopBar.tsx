import Brand from './Brand';
import LiveCallButton from './LiveCallButton';
import { NAV_ITEMS } from '../constants';
import { useActiveSection } from '../hooks';

const NAV_IDS = NAV_ITEMS.map((item) => item.id);

export default function TopBar() {
  const active = useActiveSection(NAV_IDS);

  return (
    <div className="topbar">
      <Brand href="#top" />

      <nav className="float-nav" aria-label="Services">
        {NAV_ITEMS.map((item) => (
          <a key={item.id} href={`#${item.id}`} aria-current={active === item.id ? 'true' : undefined}>
            {item.label}
          </a>
        ))}
      </nav>

      <LiveCallButton className="cta cta-primary">
        <span className="long">Request a Live Call</span>
        <span className="short mono">Live Call</span>
      </LiveCallButton>
    </div>
  );
}
