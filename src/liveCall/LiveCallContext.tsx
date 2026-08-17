import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { requestLiveCallToken, type LiveCallCredentials } from '../lib/liveCall';

type Status = 'idle' | 'connecting' | 'active' | 'error';

interface LiveCallContextValue {
  status: Status;
  error: string;
  credentials: LiveCallCredentials | null;
  startCall: () => void;
  endCall: () => void;
}

const LiveCallContext = createContext<LiveCallContextValue | null>(null);

export function LiveCallProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');
  const [credentials, setCredentials] = useState<LiveCallCredentials | null>(null);

  const startCall = useCallback(() => {
    setStatus('connecting');
    setError('');
    requestLiveCallToken()
      .then((creds) => {
        setCredentials(creds);
        setStatus('active');
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Could not start the live call.');
        setStatus('error');
      });
  }, []);

  const endCall = useCallback(() => {
    setStatus('idle');
    setCredentials(null);
    setError('');
  }, []);

  const value = useMemo(
    () => ({ status, error, credentials, startCall, endCall }),
    [status, error, credentials, startCall, endCall],
  );

  return <LiveCallContext.Provider value={value}>{children}</LiveCallContext.Provider>;
}

export function useLiveCall() {
  const ctx = useContext(LiveCallContext);
  if (!ctx) throw new Error('useLiveCall must be used within LiveCallProvider');
  return ctx;
}
