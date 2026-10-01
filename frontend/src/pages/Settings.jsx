import React, { useEffect, useState, useMemo } from 'react';
import { CalendarClock, RefreshCcw, Search, UserCircle2, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { calendarService } from '../services/api';

// BOLT OPTIMIZATION: Memoize Intl.DateTimeFormat at module scope to prevent
// repeated expensive constructor calls on every component re-render.
const fmt = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });

const Settings = () => {
  const { user } = useAuth();
  const [events, setEvents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');
  const [syncError, setSyncError] = useState(false);

  const loadEvents = async () => {
    try {
      const data = await calendarService.getEvents();
      setEvents(data.events || []);
    } catch (error) {
      console.error('Failed to load calendar events', error);
      throw error;
    }
  };

  useEffect(() => {
    loadEvents().catch(() => {});
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    setMessage('');
    setSyncError(false);
    try {
      await loadEvents();
      setMessage('Calendar refreshed.');
    } catch (error) {
      setMessage('Failed to refresh calendar');
      setSyncError(true);
    } finally {
      setSyncing(false);
    }
  };

  const filteredEvents = useMemo(() => {
    if (!searchQuery.trim()) return events;
    const q = searchQuery.toLowerCase();
    return events.filter((e) => (e.title || '').toLowerCase().includes(q));
  }, [events, searchQuery]);

  const initials = (user?.name || '?').split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase();

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-ink-900">Settings</h1>
        <p className="mt-1 text-ink-900/55">Manage your account and calendar connections.</p>
      </div>

      {/* Account */}
      <div className="card p-6 sm:p-7">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 flex-none items-center justify-center rounded-2xl bg-brand-gradient text-xl font-bold text-white">
            {initials}
          </div>
          <div>
            <h2 className="text-lg font-bold text-ink-900">{user?.name}</h2>
            <p className="flex items-center gap-1.5 text-sm text-ink-900/55">
              <UserCircle2 className="h-4 w-4" /> {user?.email}
            </p>
          </div>
        </div>
      </div>

      {/* Calendar */}
      <div className="card p-6 sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-bold text-ink-900">
              <CalendarClock className="h-5 w-5 text-primary-500" /> Calendar sync
            </h2>
            <p className="mt-1 text-sm text-ink-900/55">
              Connect Google Calendar and keep your meetings in sync.
            </p>
          </div>
          <button type="button" onClick={handleSync} disabled={syncing} aria-busy={syncing} aria-label={syncing ? 'Syncing calendar' : 'Sync calendar now'} className="btn-primary">
            <RefreshCcw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing…' : 'Sync now'}
          </button>
        </div>

        {message && (
          <p
            role="status"
            aria-live="polite"
            className={`mt-4 text-sm font-medium ${syncError ? 'text-red-600' : 'text-emerald-600'}`}
          >
            {message}
          </p>
        )}

        {events.length > 0 && (
          <div className="mt-5 space-y-2">
            <div className="relative flex items-center">
              <Search className="absolute left-3.5 h-4 w-4 text-ink-900/40 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search synced events…"
                aria-label="Filter synced events by title"
                className="w-full rounded-xl border border-ink-900/10 bg-slate-50 py-2 pl-10 pr-10 text-sm text-ink-900 placeholder:text-ink-900/40 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear event search"
                  className="absolute right-2.5 rounded-lg p-1 text-ink-900/40 hover:bg-slate-200/60 hover:text-ink-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            <p role="status" aria-live="polite" className="text-xs font-medium text-ink-900/50 px-1">
              {searchQuery.trim()
                ? `Showing ${filteredEvents.length} of ${events.length} event${events.length === 1 ? '' : 's'}`
                : `Total ${events.length} event${events.length === 1 ? '' : 's'}`}
            </p>
          </div>
        )}

        <div className="mt-4 space-y-3">
          {events.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-ink-900/10 bg-slate-50 px-5 py-8 text-center text-sm text-ink-900/50">
              No events synced yet.
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-ink-900/10 bg-slate-50 px-5 py-8 text-center text-sm text-ink-900/50">
              <p>No events found matching “{searchQuery}”.</p>
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="mt-3 inline-flex items-center gap-1.5 rounded-xl border border-ink-900/10 bg-white px-3 py-1.5 text-xs font-semibold text-primary-600 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              >
                Clear search
              </button>
            </div>
          ) : (
            filteredEvents.map((event) => (
              <div key={event.id} className="flex items-center gap-3 rounded-2xl bg-slate-50 p-3.5">
                <span className="flex h-9 w-9 flex-none items-center justify-center rounded-xl bg-primary-50 text-primary-500">
                  <CalendarClock className="h-4 w-4" />
                </span>
                <div className="min-w-0">
                  <p className="truncate font-semibold text-ink-900">{event.title}</p>
                  <p className="text-sm text-ink-900/50">
                    {fmt.format(new Date(event.start || event.start_time))}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
