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

export default function App() {
  return (
    <>
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
    </>
  );
}
