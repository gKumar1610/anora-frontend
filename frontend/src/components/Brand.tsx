import Logo from './Logo';

export default function Brand({ href = '#top' }: { href?: string }) {
  return (
    <a href={href} className="brand" aria-label="Arlong AI">
      <span className="brand-mark">
        <Logo />
      </span>
      <span className="brand-word">Arlong AI</span>
    </a>
  );
}
