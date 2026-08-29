import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import GoogleButton from '../components/GoogleButton';
import Logo from '../components/Logo';
import { Mic, Sparkles, CalendarCheck, ShieldCheck } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login: passwordLogin, googleLogin: authGoogleLogin } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSuccess = async (authResult) => {
    setError('');
    setLoading(true);
    try {
      await authGoogleLogin(authResult.code);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.message || 'Google login failed');
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await passwordLogin(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to login');
      setLoading(false);
    }
  };

  const googleLogin = useGoogleLogin({
    onSuccess: handleGoogleSuccess,
    onError: () => setError('Google login failed'),
    flow: 'auth-code',
    scope: 'openid email profile https://www.googleapis.com/auth/calendar.events',
  });

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
            <Feature icon={Mic} text="Speak naturally — no forms, no clicking" />
            <Feature icon={CalendarCheck} text="Real calendar events with smart time parsing" />
            <Feature icon={ShieldCheck} text="JWT-secured, Bcrypt-hashed, private by design" />
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
          <h2 className="text-3xl font-extrabold text-ink-900">Welcome back</h2>
          <p className="mt-2 text-ink-900/55">Sign in to pick up where you left off.</p>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
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
                  autoComplete="current-password"
                  className="input-field pr-11"
                  placeholder="••••••••"
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
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="my-6 flex items-center gap-4">
            <span className="h-px flex-1 bg-ink-900/10" />
            <span className="text-xs font-medium uppercase tracking-wide text-ink-900/40">or</span>
            <span className="h-px flex-1 bg-ink-900/10" />
          </div>

          <GoogleButton onClick={() => googleLogin()} loading={loading} label="Continue with Google Calendar" />

          <p className="mt-8 text-center text-sm text-ink-900/55">
            New here?{' '}
            <Link to="/register" className="font-semibold text-primary-600 hover:text-primary-700">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

const Feature = ({ icon: Icon, text }) => (
  <li className="flex items-start gap-3 text-sm text-white/85">
    <span className="mt-0.5 flex h-7 w-7 flex-none items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/15">
      <Icon className="h-4 w-4 text-primary-200" />
    </span>
    {text}
  </li>
);

export default Login;
