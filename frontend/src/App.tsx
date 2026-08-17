import { lazy, Suspense } from 'react';
import TopBar from './components/TopBar';
import Intro from './components/Intro';
import Hero from './components/Hero';
import Problem from './components/Problem';
import HowItWorks from './components/HowItWorks';
import Modules from './components/Modules';
import Differentiation from './components/Differentiation';
import WhoItsFor from './components/WhoItsFor';
import FinalCta from './components/FinalCta';
import Footer from './components/Footer';
import { LiveCallProvider, useLiveCall } from './liveCall/LiveCallContext';

// LiveCallModal pulls in the LiveKit SDK — keep it out of the initial bundle
// and only fetch it once someone actually opens a call.
const LiveCallModal = lazy(() => import('./components/LiveCallModal'));

function LiveCallModalGate() {
  const { status } = useLiveCall();
  if (status === 'idle') return null;
  return (
    <Suspense fallback={null}>
      <LiveCallModal />
    </Suspense>
  );
}

export default function App() {
  return (
    <LiveCallProvider>
      <TopBar />
      <main>
        <Intro />
        <Hero />
        <Problem />
        <HowItWorks />
        <Modules />
        <Differentiation />
        <WhoItsFor />
        <FinalCta />
      </main>
      <Footer />
      <LiveCallModalGate />
    </LiveCallProvider>
  );
}
