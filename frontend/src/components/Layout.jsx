import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { CalendarDays, Settings as SettingsIcon, LogOut, LayoutGrid } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';

const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) =>
    path === '/'
      ? location.pathname === '/'
      : location.pathname.includes(path);

  const initials = (user?.name || '?')
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="min-h-screen bg-slate-50 text-ink-900">
      {/* Decorative background blobs */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-primary-300/30 blur-3xl animate-float" />
        <div className="absolute top-1/3 -right-24 h-80 w-80 rounded-full bg-fuchsia-300/25 blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </div>

      {/* ===== Desktop Sidebar ===== */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-sidebar-gradient text-white md:flex">
        <div className="px-5 py-6">
          <Logo />
        </div>

        <nav className="mt-2 flex-1 space-y-1 px-3">
          <SideLink to="/" active={isActive('/')} icon={LayoutGrid} label="Dashboard" />
          <SideLink to="/settings" active={isActive('/settings')} icon={SettingsIcon} label="Settings" />
        </nav>

        <div className="m-3 rounded-2xl bg-white/5 p-3 ring-1 ring-white/10">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-gradient text-sm font-bold">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{user?.name}</p>
              <p className="truncate text-xs text-white/60">{user?.email}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-white/10 py-2 text-sm font-medium text-white/90 transition hover:bg-white/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-300"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </aside>

      {/* ===== Main ===== */}
      <div className="md:pl-64">
        <main className="mx-auto max-w-6xl px-4 pb-28 pt-8 sm:px-6 lg:px-10 md:pb-12">
          <Outlet />
        </main>
      </div>

      {/* ===== Mobile Bottom Nav (a11y preserved) ===== */}
      <nav aria-label="Mobile navigation" className="fixed inset-x-0 bottom-0 z-20 border-t border-ink-900/5 bg-white/90 backdrop-blur-xl md:hidden">
        <div className="mx-auto flex max-w-md items-stretch justify-around py-1.5">
          <Link
            to="/"
            aria-label="Meetings dashboard"
            className={`flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-xs font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 ${
              isActive('/') ? 'text-primary-600' : 'text-ink-900/55'
            }`}
          >
            <CalendarDays className="h-6 w-6" />
            <span>Meetings</span>
          </Link>
          <Link
            to="/settings"
            aria-label="Settings"
            className={`flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-xs font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 ${
              isActive('/settings') ? 'text-primary-600' : 'text-ink-900/55'
            }`}
          >
            <SettingsIcon className="h-6 w-6" />
            <span>Settings</span>
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            aria-label="Log out"
            className="flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-xs font-medium text-ink-900/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
          >
            <LogOut className="h-6 w-6" />
            <span>Logout</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

const SideLink = ({ to, active, icon: Icon, label }) => (
  <Link
    to={to}
    className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-300 ${
      active
        ? 'bg-white/15 text-white shadow-inner'
        : 'text-white/70 hover:bg-white/10 hover:text-white'
    }`}
  >
    <Icon className={`h-5 w-5 ${active ? 'text-primary-300' : 'text-white/60 group-hover:text-white'}`} />
    {label}
  </Link>
);

export default Layout;
