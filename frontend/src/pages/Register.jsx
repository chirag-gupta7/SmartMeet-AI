import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from '../components/Logo';
import { Mic, Sparkles, CalendarCheck, ShieldCheck } from 'lucide-react';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(name, email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to register');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-2">
      {/* ===== Brand Panel ===== */}
      <div className="relative hidden overflow-hidden bg-sidebar-gradient lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="pointer-events-none absolute -left-16 -top-16 h-72 w-72 rounded-full bg-primary-500/30 blur-3xl animate-float" />
        <div className="pointer-events-none absolute -bottom-20 right-0 h-80 w-80 rounded-full bg-fuchsia-500/25 blur-3xl animate-float" style={{ animationDelay: '2.5s' }} />

        <div className="relative">
          <Logo />
        </div>

        <div className="relative max-w-md animate-fade-in-up">
          <span className="pill bg-white/10 text-primary-200 ring-1 ring-white/15">
            <Sparkles className="h-3.5 w-3.5" /> Voice-first scheduling
          </span>
          <h1 className="mt-5 text-4xl font-extrabold leading-tight text-white">
            Meetings you can just <span className="text-primary-300">talk to.</span>
          </h1>
          <p className="mt-4 text-white/70">
            Dictate a meeting in plain language and let the AI schedule it, sync your calendar, and confirm out loud.
          </p>

          <ul className="mt-8 space-y-4">
            <li className="flex items-start gap-3 text-sm text-white/85">
              <span className="mt-0.5 flex h-7 w-7 flex-none items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15">
                <Mic className="h-4 w-4 text-primary-200" />
              </span>
              Speak naturally — no forms, no clicking
            </li>
            <li className="flex items-start gap-3 text-sm text-white/85">
              <span className="mt-0.5 flex h-7 w-7 flex-none items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15">
                <CalendarCheck className="h-4 w-4 text-primary-200" />
              </span>
              Real calendar events with smart time parsing
            </li>
            <li className="flex items-start gap-3 text-sm text-white/85">
              <span className="mt-0.5 flex h-7 w-7 flex-none items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15">
                <ShieldCheck className="h-4 w-4 text-primary-200" />
              </span>
              JWT-secured, Bcrypt-hashed, private by design
            </li>
          </ul>
        </div>

        <p className="relative text-sm text-white/40">© {new Date().getFullYear()} SmartMeet AI</p>
      </div>

      {/* ===== Form Panel ===== */}
      <div className="flex items-center justify-center bg-slate-50 px-4 py-12 sm:px-8">
        <div className="w-full max-w-md animate-fade-in">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <Logo variant="dark" withText={false} />
          </div>
          <h2 className="text-3xl font-extrabold text-ink-900">Create your account</h2>
          <p className="mt-2 text-ink-900/55">It takes less than a minute to get started.</p>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div>
              <label className="label-text" htmlFor="name">Name</label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
                className="input-field"
                placeholder="Jane Doe"
              />
            </div>

            <div>
              <label className="label-text" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="input-field"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="label-text" htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  minLength={6}
                  className="input-field pr-11"
                  placeholder="At least 6 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  className="absolute inset-y-0 right-1 my-1 flex items-center rounded-lg px-2.5 text-xs font-semibold text-ink-900/45 hover:text-ink-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                  aria-label={showPw ? 'Hide password' : 'Show password'}
                  aria-pressed={showPw}
                >
                  {showPw ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-ink-900/55">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-primary-600 hover:text-primary-700">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
