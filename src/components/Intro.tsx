import { useLayoutEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { SplitText } from 'gsap/SplitText';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(SplitText, ScrollTrigger);

// Decorative only — the four shipped/roadmap modules plus the candidate
// touchpoints from anora-ai-docs/suggestions.md. None of the latter are
// committed scope; they exist here only as atmosphere behind the wordmark.
// Top row, bottom row, and two bubbles flanking each side of the wordmark at
// mid-height (just outside its actual text width) — so the space left/right
// of "Anora AI" fills in, not just the far corners.
const BUBBLES: { label: string; top: number; left: number; size: 'sm' | 'md' | 'lg' }[] = [
  { label: 'Voice', top: 8, left: 8, size: 'lg' },
  { label: 'Dashboard', top: 14, left: 32, size: 'md' },
  { label: 'Reserve', top: 10, left: 68, size: 'md' },
  { label: 'Tables', top: 16, left: 92, size: 'lg' },
  { label: 'Waitlist', top: 38, left: 16, size: 'sm' },
  { label: 'WhatsApp', top: 62, left: 14, size: 'sm' },
  { label: 'Feedback', top: 42, left: 86, size: 'sm' },
  { label: 'Guest Profiles', top: 58, left: 84, size: 'md' },
  { label: 'Digital Menu', top: 84, left: 12, size: 'sm' },
  { label: 'Pre-Ordering', top: 90, left: 38, size: 'sm' },
  { label: 'Event Enquiries', top: 86, left: 64, size: 'md' },
  { label: 'Loyalty', top: 92, left: 88, size: 'sm' },
];

const BUBBLE_OPACITY: Record<'sm' | 'md' | 'lg', number> = { sm: 0.24, md: 0.38, lg: 0.55 };

export default function Intro() {
  const rootRef = useRef<HTMLElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const ruleRef = useRef<HTMLSpanElement>(null);
  const taglineRef = useRef<HTMLParagraphElement>(null);
  const scrollRef = useRef<HTMLAnchorElement>(null);
  const bubblesRef = useRef<HTMLDivElement>(null);
  const bubbleEls = useRef<(HTMLSpanElement | null)[]>([]);

  useLayoutEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let split: SplitText | undefined;
    const bubbles = bubbleEls.current.filter((el): el is HTMLSpanElement => el !== null);

    const ctx = gsap.context(() => {
      if (!headingRef.current) return;

      split = new SplitText(headingRef.current, { type: 'chars', charsClass: 'char' });

      gsap.set(bubbles, {
        xPercent: -50,
        yPercent: -50,
        scale: 0.85,
        opacity: 0,
        y: () => gsap.utils.random(70, 160),
      });

      if (reduced) {
        gsap.set(split.chars, { opacity: 1 });
        gsap.set([ruleRef.current, taglineRef.current, scrollRef.current], { opacity: 1 });
        gsap.set(ruleRef.current, { scaleX: 0.14 });
        bubbles.forEach((el) => {
          const size = el.dataset.size as 'sm' | 'md' | 'lg';
          gsap.set(el, { opacity: BUBBLE_OPACITY[size], scale: 1, y: 0 });
        });
        return;
      }

      gsap.set(split.chars, { opacity: 0, yPercent: 110, rotateX: -70, filter: 'blur(10px)' });

      const tl = gsap.timeline({ delay: 0.15 });

      tl.to(ruleRef.current, { scaleX: 1, duration: 0.6, ease: 'power3.out' })
        .to(
          split.chars,
          {
            opacity: 1,
            yPercent: 0,
            rotateX: 0,
            filter: 'blur(0px)',
            duration: 1,
            stagger: 0.035,
            ease: 'power4.out',
          },
          '-=0.25',
        )
        .to(ruleRef.current, { scaleX: 0.14, duration: 0.5, ease: 'power2.inOut' }, '-=0.5')
        .to(taglineRef.current, { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }, '-=0.35')
        .to(scrollRef.current, { opacity: 1, duration: 0.6, ease: 'power1.out' }, '-=0.2')
        .to(
          bubbles,
          {
            opacity: (_i, target: HTMLElement) => BUBBLE_OPACITY[target.dataset.size as 'sm' | 'md' | 'lg'],
            scale: 1,
            y: 0,
            duration: 1.4,
            stagger: 0.09,
            ease: 'power3.out',
          },
          '+=0.1',
        );

      // continuous ambient float, starting only once each bubble has finished
      // rising into place — independent x/y/rotation loops of differing
      // duration so the motion never repeats in sync and reads as genuine
      // drifting rather than a simple bob.
      const driftStart = 3.9; // ≈ when the last bubble's rise-in settles
      bubbles.forEach((el, i) => {
        gsap.to(el, {
          y: gsap.utils.random(-70, 70),
          duration: gsap.utils.random(5, 9),
          delay: driftStart + i * 0.09,
          ease: 'sine.inOut',
          yoyo: true,
          repeat: -1,
        });
        gsap.to(el, {
          x: gsap.utils.random(-60, 60),
          duration: gsap.utils.random(8, 14),
          delay: driftStart + 0.2 + i * 0.09,
          ease: 'sine.inOut',
          yoyo: true,
          repeat: -1,
        });
        gsap.to(el, {
          rotation: gsap.utils.random(-10, 10),
          duration: gsap.utils.random(7, 11),
          delay: driftStart + 0.1 + i * 0.09,
          ease: 'sine.inOut',
          yoyo: true,
          repeat: -1,
        });
      });

      gsap.to(innerRef.current, {
        opacity: 0,
        scale: 0.92,
        y: -60,
        ease: 'none',
        scrollTrigger: {
          trigger: rootRef.current,
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      });

      gsap.to(bubblesRef.current, {
        opacity: 0,
        y: -100,
        ease: 'none',
        scrollTrigger: {
          trigger: rootRef.current,
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      });
    }, rootRef);

    return () => {
      ctx.revert();
      split?.revert();
    };
  }, []);

  return (
    <section className="intro" id="top" ref={rootRef}>
      <div className="intro-bubbles" ref={bubblesRef} aria-hidden="true">
        {BUBBLES.map((b, i) => (
          <span
            key={b.label}
            className={`bubble-float bubble-${b.size}`}
            data-size={b.size}
            style={{ top: `${b.top}%`, left: `${b.left}%` }}
            ref={(el) => {
              bubbleEls.current[i] = el;
            }}
          >
            {b.label}
          </span>
        ))}
      </div>

      <div className="intro-inner" ref={innerRef}>
        <span className="intro-rule" ref={ruleRef} />
        <h1 className="intro-word" ref={headingRef}>
          Anora AI
        </h1>
        <p className="intro-tagline" ref={taglineRef}>
          Voice For Your Brand
        </p>
      </div>
      <a className="intro-scroll" href="#hero" aria-label="Scroll to explore" ref={scrollRef}>
        <span className="intro-scroll-line" />
      </a>
    </section>
  );
}
