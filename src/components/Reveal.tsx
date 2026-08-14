import { useEffect, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';

interface RevealProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export default function Reveal({ children, className = '', style }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setInView(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: '0px 0px -8% 0px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={`reveal ${inView ? 'in-view' : ''} ${className}`.trim()} style={style}>
      {children}
    </div>
  );
}
