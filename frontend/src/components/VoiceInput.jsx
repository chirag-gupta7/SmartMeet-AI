import React, { useEffect, useState, useRef } from 'react';
import { Mic, Square, Volume2, ArrowRight } from 'lucide-react';
import { voiceService } from '../services/voiceService';
import api from '../services/api';

const VoiceInput = ({ onTranscript, onProcessing, responseMessage, authUrl }) => {
  const [isListening, setIsListening] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  const [isFirstInteraction, setIsFirstInteraction] = useState(true);

  const audioRef = useRef(new Audio());

  useEffect(() => {
    if (!voiceService.isSupported()) {
      setError('Voice recognition is not supported in this browser. Please use Chrome.');
    }
    const audioEl = audioRef.current;
    return () => {
      if (audioEl) {
        audioEl.pause();
        audioEl.src = '';
      }
    };
  }, []);

  const playAudio = (base64Audio) =>
    new Promise((resolve) => {
      if (!base64Audio) return resolve();
      audioRef.current.pause();
      audioRef.current.src = `data:audio/mp3;base64,${base64Audio}`;
      setIsPlayingAudio(true);
      audioRef.current.onended = () => {
        setIsPlayingAudio(false);
        resolve();
      };
      audioRef.current.play().catch(() => {
        setIsPlayingAudio(false);
        resolve();
      });
    });

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlayingAudio(false);
    }
  };

  const handleInteraction = async () => {
    setError(null);
    if (isListening) {
      voiceService.stopListening();
      setIsListening(false);
      onProcessing(false);
      return;
    }

    if (isFirstInteraction) {
      setIsFirstInteraction(false);
      onProcessing(true);
      try {
        const response = await api.get('/api/voice/greeting');
        const data = response.data;
        if (data.success && data.audio_base64) {
          await playAudio(data.audio_base64);
          if (!audioRef.current.paused) return;
          await startListeningInternal();
        } else {
          await startListeningInternal();
        }
      } catch (err) {
        console.error('Greeting failed', err);
        await startListeningInternal();
      }
      return;
    }

    if (isPlayingAudio) stopAudio();
    await startListeningInternal();
  };

  const getAriaLabel = () => {
    if (isListening) return 'Stop listening';
    if (isPlayingAudio) return 'Interrupt AI response';
    if (isFirstInteraction) return 'Start voice assistant';
    return 'Start voice input';
  };

  const startListeningInternal = async () => {
    try {
      setIsListening(true);
      onProcessing(true);
      const result = await voiceService.startListening();
      setTranscript(result);
      onTranscript(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsListening(false);
      onProcessing(false);
    }
  };

  const stateClasses = isListening
    ? 'bg-red-500 hover:bg-red-600'
    : isPlayingAudio
      ? 'bg-emerald-500 hover:bg-emerald-600'
      : 'bg-brand-gradient hover:opacity-90';

  return (
    <div className="space-y-5">
      <div className="flex flex-col items-center">
        <div className="relative">
          {isListening && (
            <span className="absolute inset-0 rounded-full bg-red-400/60 animate-ring-pulse" />
          )}
          <button
            type="button"
            onClick={handleInteraction}
            disabled={Boolean(error)}
            aria-label={getAriaLabel()}
            title={getAriaLabel()}
            className={`relative flex h-24 w-24 items-center justify-center rounded-full text-white shadow-glow transition-all duration-300 focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-300 ${stateClasses} ${error ? 'cursor-not-allowed opacity-50' : 'cursor-pointer hover:scale-105'}`}
          >
            {isListening ? (
              <Square className="h-9 w-9 fill-current" />
            ) : isPlayingAudio ? (
              <Volume2 className="h-9 w-9" />
            ) : (
              <Mic className="h-9 w-9" />
            )}
          </button>
        </div>

        <p className="mt-4 text-sm font-medium text-ink-900/70">
          {isListening && <span className="text-red-500 animate-pulse">Listening…</span>}
          {isPlayingAudio && <span className="text-emerald-600">AI is speaking… (tap to interrupt)</span>}
          {!isListening && !isPlayingAudio && !transcript && !error && (
            <span className="text-ink-900/50">{isFirstInteraction ? 'Tap to start the assistant' : 'Tap to speak again'}</span>
          )}
        </p>
      </div>

      {transcript && (
        <div className="rounded-2xl border border-ink-900/5 bg-slate-50 p-4">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-900/40">You said</p>
          <p className="text-ink-900">“{transcript}”</p>
        </div>
      )}

      {(responseMessage || authUrl) && (
        <div className="rounded-2xl border border-primary-100 bg-primary-50/60 p-4">
          {responseMessage && <p className="text-sm text-ink-900">{responseMessage}</p>}
          {authUrl && (
            <a
              href={authUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:bg-primary-700"
            >
              Authorize Google Calendar <ArrowRight className="h-4 w-4" />
            </a>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};

export default VoiceInput;
