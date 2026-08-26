import React from 'react';

const Logo = ({ className = 'h-8 w-8', variant = 'light', withText = true }) => {
  const textClass =
    variant === 'dark'
      ? 'bg-gradient-to-r from-primary-600 to-violet-600 bg-clip-text text-transparent'
      : 'bg-gradient-to-r from-white to-primary-200 bg-clip-text text-transparent';

  return (
    <span className="inline-flex items-center gap-2.5">
      <svg className={className} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
          <linearGradient id="sm-logo" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4f46e5" />
            <stop offset="1" stopColor="#7c3aed" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="9" fill="url(#sm-logo)" />
        <g stroke="white" strokeWidth="2" strokeLinecap="round" fill="none">
          <rect x="11.5" y="7" width="9" height="15" rx="4.5" />
          <path d="M16 22.5v2.5" />
        </g>
      </svg>
      {withText && (
        <span className={`text-lg font-extrabold tracking-tight leading-none ${textClass}`}>
          SmartMeet AI
        </span>
      )}
    </span>
  );
};

export default Logo;
