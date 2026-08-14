import Brand from './Brand';
import { CONTACT_MAILTO, DEMO_MAILTO } from '../constants';

export default function Footer() {
  return (
    <footer>
      <div className="wrap">
        <div className="foot-top">
          <div className="foot-brand">
            <Brand href="#top" />
            <p>Front-of-house operations, answered. Hyderabad, India.</p>
          </div>

          <div className="foot-col">
            <div className="eyebrow">Product</div>
            <ul>
              <li>
                <a href="#voice">Arlong Voice</a>
              </li>
              <li>
                <a href="#dashboard">Arlong Dashboard</a>
              </li>
              <li>
                <a href="#reserve">Arlong Reserve</a>
              </li>
              <li>
                <a href="#tables">Arlong Tables</a>
              </li>
            </ul>
          </div>

          <div className="foot-col">
            <div className="eyebrow">Page</div>
            <ul>
              <li>
                <a href="#problem">The problem</a>
              </li>
              <li>
                <a href="#how-it-works">How it works</a>
              </li>
              <li>
                <a href="#why">Why it works</a>
              </li>
              <li>
                <a href="#who">Who it's for</a>
              </li>
            </ul>
          </div>

          <div className="foot-col">
            <div className="eyebrow">Get in touch</div>
            <ul>
              <li>
                <a href={DEMO_MAILTO}>Request a Live Call</a>
              </li>
              <li>
                <a href={CONTACT_MAILTO}>General enquiries</a>
              </li>
            </ul>
          </div>
        </div>

        <div className="foot-bottom">
          <span>© 2026 ARLONG AI</span>
          <span>FRONT OF HOUSE, OPERATED</span>
        </div>
      </div>
    </footer>
  );
}
