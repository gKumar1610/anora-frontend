import type { ReactNode } from 'react';
import { useLiveCall } from '../liveCall/LiveCallContext';

interface LiveCallButtonProps {
  className?: string;
  children: ReactNode;
}

export default function LiveCallButton({ className, children }: LiveCallButtonProps) {
  const { status, startCall } = useLiveCall();
  return (
    <button type="button" className={className} onClick={startCall} disabled={status === 'connecting'}>
      {children}
    </button>
  );
}
