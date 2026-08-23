import React, { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { googleLogin } = useAuth();
  const calledRef = useRef(false); // Prevent double-fire in React Strict Mode

  useEffect(() => {
    if (calledRef.current) return;

    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const error = params.get('error');

    if (error) {
      console.error('Google Auth error:', error);
      navigate('/', { replace: true });
      return;
    }

    // Route through AuthContext so the token AND user state update.
    if (code) {
      calledRef.current = true;
      googleLogin(code)
        .then(() => navigate('/', { replace: true }))
        .catch((err) => {
          console.error('Google login failed:', err);
          navigate('/', { replace: true });
        });
    }
  }, [location, navigate, googleLogin]);

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-xl font-semibold animate-pulse">Connecting to Google Calendar...</div>
    </div>
  );
};

export default OAuthCallback;
