import { useEffect, useState } from 'react';
import App from './App';
import Preloader from './components/Preloader';

const LOAD_DURATION = 3000;
const FADE_DURATION = 400;

export default function Root() {
  const [phase, setPhase] = useState<'loading' | 'leaving' | 'done'>('loading');

  useEffect(() => {
    const showApp = setTimeout(() => setPhase('leaving'), LOAD_DURATION);
    return () => clearTimeout(showApp);
  }, []);

  useEffect(() => {
    if (phase !== 'leaving') return;
    const unmount = setTimeout(() => setPhase('done'), FADE_DURATION);
    return () => clearTimeout(unmount);
  }, [phase]);

  if (phase === 'done') return <App />;
  return <Preloader leaving={phase === 'leaving'} />;
}
