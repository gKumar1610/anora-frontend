import { useEffect, useMemo } from 'react';
import {
  BarVisualizer,
  LiveKitRoom,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  useVoiceAssistant,
} from '@livekit/components-react';
import { useLiveCall } from '../liveCall/LiveCallContext';

export default function LiveCallModal() {
  const { status, error, credentials, endCall } = useLiveCall();
  const open = status !== 'idle';

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') endCall();
    };
    window.addEventListener('keydown', onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, endCall]);

  if (!open) return null;

  return (
    <div className="live-call-overlay" role="dialog" aria-modal="true" aria-label="Live call with Nami Voice">
      <div className="live-call-panel">
        <button type="button" className="live-call-close" onClick={endCall} aria-label="Close">
          ×
        </button>

        {status === 'connecting' && (
          <div className="live-call-state">
            <span className="live-dot" />
            <p className="mono">Connecting to Nami Voice…</p>
          </div>
        )}

        {status === 'error' && (
          <div className="live-call-state">
            <p className="live-call-error-title">Couldn't connect</p>
            <p className="live-call-error-detail">{error}</p>
          </div>
        )}

        {status === 'active' && credentials && (
          <LiveKitRoom
            token={credentials.participant_token}
            serverUrl={credentials.server_url}
            connect
            audio
            video={false}
            onDisconnected={endCall}
            onError={() => {
              /* surfaced via connectionState below */
            }}
            className="live-call-room"
            data-lk-theme="default"
          >
            <LiveCallRoom />
            <RoomAudioRenderer />
          </LiveKitRoom>
        )}
      </div>
    </div>
  );
}

function LiveCallRoom() {
  const { state, audioTrack } = useVoiceAssistant();
  const label = useMemo(() => String(state).replace(/_/g, ' '), [state]);

  return (
    <div className="live-call-room-inner">
      <div className="live-call-head">
        <span className="live-dot" />
        <span className="mono">NAMI VOICE · {label}</span>
      </div>
      <div className="live-call-viz">
        <BarVisualizer state={state} trackRef={audioTrack} barCount={28} />
      </div>
      <p className="live-call-hint">
        Speak naturally — you're talking to the same agent that answers Lili Cantonese Kitchen's phone.
      </p>
      <VoiceAssistantControlBar controls={{ microphone: true, leave: true }} />
    </div>
  );
}
