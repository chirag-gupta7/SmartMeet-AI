import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

jest.mock('../services/api', () => ({
  authService: {
    googleLogin: jest.fn(),
    login: jest.fn(),
    register: jest.fn(),
    getCurrentUser: jest.fn(),
  },
  meetingService: {},
  calendarService: {},
  default: {},
}));

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

jest.mock('@react-oauth/google', () => ({
  GoogleOAuthProvider: ({ children }) => children,
  useGoogleLogin: jest.fn(),
}));

import { authService } from '../services/api';
import { useGoogleLogin } from '@react-oauth/google';
import { AuthProvider } from '../context/AuthContext';
import Login from '../pages/Login';
import OAuthCallback from '../components/OAuthCallback';

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  // CRA's resetMocks wipes factory implementations, so set them per test.
  authService.getCurrentUser.mockResolvedValue({ user: { id: 'u1', name: 'Test' } });
});

describe('Google login flow regression (H2a)', () => {
  test('Login page exchanges the code via authService and stores the token', async () => {
    let capturedOnSuccess;
    useGoogleLogin.mockImplementation(({ onSuccess }) => {
      capturedOnSuccess = onSuccess;
      return jest.fn();
    });
    authService.googleLogin.mockResolvedValue({
      token: 'tok-123',
      user: { id: 'u1', name: 'Test' },
    });

    render(
      <AuthProvider>
        <MemoryRouter>
          <Login />
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('SmartMeet AI')).toBeInTheDocument());

    // Simulate the popup flow handing back an authorization code.
    await capturedOnSuccess({ code: 'abc-123' });

    expect(authService.googleLogin).toHaveBeenCalledWith('abc-123');
    expect(localStorage.getItem('token')).toBe('tok-123');
  });

  test('OAuthCallback routes through AuthContext and navigates to /', async () => {
    localStorage.setItem('token', 'existing-token');
    authService.googleLogin.mockResolvedValue({
      token: 'tok-456',
      user: { id: 'u2', name: 'Test2' },
    });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/auth/callback?code=xyz-789']}>
          <OAuthCallback />
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => expect(authService.googleLogin).toHaveBeenCalledWith('xyz-789'));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true }));
    expect(localStorage.getItem('token')).toBe('tok-456');
  });

  test('OAuthCallback navigates home on provider error without calling the API', async () => {
    localStorage.setItem('token', 'existing-token');

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/auth/callback?error=access_denied']}>
          <OAuthCallback />
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true }));
    expect(authService.googleLogin).not.toHaveBeenCalled();
  });
});
