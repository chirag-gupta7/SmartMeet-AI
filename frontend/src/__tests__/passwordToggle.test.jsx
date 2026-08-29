import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: jest.fn(),
    googleLogin: jest.fn(),
    register: jest.fn(),
  }),
}));

jest.mock('@react-oauth/google', () => ({
  useGoogleLogin: () => jest.fn(),
}));

import Login from '../pages/Login';
import Register from '../pages/Register';

describe('Password visibility toggle accessibility', () => {
  test('Login password toggle button updates aria-pressed and aria-label on click', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    const toggleBtn = screen.getByRole('button', { name: 'Show password' });
    expect(toggleBtn).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(toggleBtn);

    expect(toggleBtn).toHaveAttribute('aria-pressed', 'true');
    expect(toggleBtn).toHaveAttribute('aria-label', 'Hide password');
  });

  test('Register password toggle button updates aria-pressed and aria-label on click', () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>
    );

    const toggleBtn = screen.getByRole('button', { name: 'Show password' });
    expect(toggleBtn).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(toggleBtn);

    expect(toggleBtn).toHaveAttribute('aria-pressed', 'true');
    expect(toggleBtn).toHaveAttribute('aria-label', 'Hide password');
  });
});
