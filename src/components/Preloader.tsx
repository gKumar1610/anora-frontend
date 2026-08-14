export default function Preloader({ leaving = false }: { leaving?: boolean }) {
  return (
    <div className={`preloader ${leaving ? 'leaving' : ''}`.trim()} role="status" aria-label="Loading Anora AI">
      <div className="preloader-dots" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  );
}
