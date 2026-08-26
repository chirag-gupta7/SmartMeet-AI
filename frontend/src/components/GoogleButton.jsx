import React from 'react';

const GoogleButton = ({ onClick, label, loading, disabled }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled || loading}
    className="flex w-full items-center justify-center gap-3 rounded-xl border border-ink-900/10 bg-white px-4 py-2.5 text-sm font-semibold text-ink-800 shadow-sm transition hover:bg-slate-50 hover:shadow-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 focus-visible:ring-offset-2 disabled:opacity-50"
  >
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a2.66 2.66 0 0 1-1.15 1.75v1.45h1.85c1.08-.99 1.94-2.55 1.94-5.21Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.65l-1.85-1.45c-.98.66-2.23 1.06-3.43 1.06-2.64 0-4.87-1.78-5.67-4.18H4.39v1.5A10 10 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M6.33 14.78a6 6 0 0 1 0-3.56v-1.5H4.39a10 10 0 0 0 0 8.2l1.94-1.5Z" />
      <path fill="#EA4335" d="M12 5.38c1.49 0 2.83.51 3.89 1.52l1.46-1.46A9.97 9.97 0 0 0 12 2a10 10 0 0 0-7.61 3.52l1.94 1.5C7.13 7.16 9.36 5.38 12 5.38Z" />
    </svg>
    {loading ? 'Connecting…' : label}
  </button>
);

export default GoogleButton;
