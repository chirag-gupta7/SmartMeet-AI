import React, { useEffect, useState } from 'react';
import { CalendarDays, Plus, Clock, CalendarCheck, Sparkles, ArrowRight, X } from 'lucide-react';
import VoiceInput from '../components/VoiceInput';
import { meetingService } from '../services/api';

// BOLT OPTIMIZATION: Module-scoped Intl.DateTimeFormat reuse prevents repeated
// object creation overhead during list rendering of meetings.
const fmt = new Intl.DateTimeFormat(undefined, { weekday: 'short', hour: 'numeric', minute: '2-digit' });
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

const startOfDay = (d) => { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; };
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };

const Dashboard = () => {
  const [meetings, setMeetings] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [showVoiceInput, setShowVoiceInput] = useState(false);
  const [responseMessage, setResponseMessage] = useState('');
  const [authUrl, setAuthUrl] = useState(null);

  useEffect(() => { loadMeetings(); }, []);

  const loadMeetings = async () => {
    try {
      const data = await meetingService.getMeetings();
      setMeetings(data.meetings || []);
    } catch (error) {
      console.error('Failed to load meetings:', error);
    }
  };

  const sorted = [...meetings].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

  const now = new Date();
  const today = sorted.filter((m) => {
    const d = startOfDay(new Date(m.start_time));
    const t = startOfDay(now);
    return d.getTime() === t.getTime();
  });
  const week = sorted.filter((m) => {
    const d = startOfDay(new Date(m.start_time)).getTime();
    return d >= startOfDay(now).getTime() && d <= startOfDay(addDays(now, 7)).getTime();
  });

  const handleVoiceTranscript = async (transcript) => {
    try {
      setProcessing(true);
      const result = await meetingService.processVoiceCommand(transcript);
      setResponseMessage(result?.message || '');

      if (result?.action === 'auth_required' && result?.auth_url) {
        setAuthUrl(result.auth_url);
        return;
      }
      setAuthUrl(null);
      if (result?.success) {
        await loadMeetings();
        setShowVoiceInput(false);
      }
    } catch (error) {
      console.error('Failed to process command:', error);
    } finally {
      setProcessing(false);
    }
  };

  const greeting = now.getHours() < 12 ? 'Good morning' : now.getHours() < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4 animate-fade-in">
        <div>
          <p className="text-sm font-medium text-primary-600">{greeting} 👋</p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-ink-900">Your meetings</h1>
        </div>
        <button
          type="button"
          onClick={() => setShowVoiceInput((v) => !v)}
          aria-expanded={showVoiceInput}
          aria-controls="voice-scheduler-panel"
          className="btn-primary"
        >
          {showVoiceInput ? <X className="h-5 w-5" /> : <Plus className="h-5 w-5" />}
          {showVoiceInput ? 'Close scheduler' : 'Schedule a meeting'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3 animate-fade-in-up">
        <StatCard icon={CalendarDays} label="Total meetings" value={meetings.length} tint="primary" />
        <StatCard icon={CalendarCheck} label="Happening today" value={today.length} tint="emerald" />
        <StatCard icon={Clock} label="Next 7 days" value={week.length} tint="violet" />
      </div>

      {/* Voice hero */}
      {showVoiceInput && (
        <div id="voice-scheduler-panel" className="card overflow-hidden animate-fade-in-up">
          <div className="bg-brand-gradient px-6 py-5 sm:px-8">
            <div className="flex items-center gap-2 text-white">
              <Sparkles className="h-5 w-5" />
              <h2 className="text-lg font-bold">Schedule with your voice</h2>
            </div>
            <p className="mt-1 text-sm text-white/75">
              Tap the mic and say something like “Sync with design at 2pm tomorrow for 45 minutes”.
            </p>
          </div>
          <div className="px-6 py-8 sm:px-8">
            <VoiceInput
              onTranscript={handleVoiceTranscript}
              onProcessing={setProcessing}
              responseMessage={responseMessage}
              authUrl={authUrl}
            />
            {processing && <p className="mt-4 text-center text-sm text-ink-900/50">Processing your request…</p>}
          </div>
        </div>
      )}

      {/* Meeting list */}
      <div className="space-y-3">
        {sorted.length === 0 ? (
          <div className="card flex flex-col items-center px-6 py-14 text-center animate-fade-in">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-50 text-primary-500">
              <CalendarDays className="h-8 w-8" />
            </div>
            <h3 className="mt-5 text-lg font-semibold text-ink-900">No meetings scheduled</h3>
            <p className="mt-1 max-w-sm text-sm text-ink-900/55">
              Hit “Schedule a meeting” and tell the assistant what you need — it’ll do the rest.
            </p>
          </div>
        ) : (
          sorted.map((m, i) => <MeetingCard key={m.id} meeting={m} style={{ animationDelay: `${i * 60}ms` }} />)
        )}
      </div>
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, tint }) => {
  const tints = {
    primary: 'bg-primary-50 text-primary-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    violet: 'bg-violet-50 text-violet-600',
  };
  return (
    <div className="card flex items-center gap-4 p-5">
      <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${tints[tint]}`}>
        <Icon className="h-6 w-6" />
      </span>
      <div>
        <p className="text-2xl font-extrabold leading-none text-ink-900">{value}</p>
        <p className="mt-1 text-sm text-ink-900/55">{label}</p>
      </div>
    </div>
  );
};

const MeetingCard = ({ meeting, style }) => {
  const d = new Date(meeting.start_time);
  const day = d.getDate();
  const month = MONTHS[d.getMonth()];
  const endTime = new Date(d.getTime() + (meeting.duration || 30) * 60000);
  return (
    <div
      className="card group flex items-center gap-4 p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-glow animate-fade-in-up"
      style={style}
    >
      <div className="flex h-16 w-16 flex-none flex-col items-center justify-center rounded-2xl bg-sidebar-gradient text-white">
        <span className="text-lg font-extrabold leading-none">{day}</span>
        <span className="text-[10px] font-bold tracking-widest">{month}</span>
      </div>

      <div className="min-w-0 flex-1">
        <h3 className="truncate text-base font-semibold text-ink-900">{meeting.title}</h3>
        <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-900/55">
          <Clock className="h-4 w-4" />
          {fmt.format(d)} – {fmt.format(endTime)}
        </p>
        {meeting.description && (
          <p className="mt-1 line-clamp-1 text-sm text-ink-900/45">{meeting.description}</p>
        )}
      </div>

      <span className="pill bg-primary-50 text-primary-700">{meeting.duration || 30} min</span>

      <ArrowRight className="hidden h-5 w-5 flex-none text-ink-900/25 transition group-hover:translate-x-1 group-hover:text-primary-500 sm:block" />
    </div>
  );
};

export default Dashboard;
