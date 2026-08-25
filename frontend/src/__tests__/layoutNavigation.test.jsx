import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../components/Layout';

jest.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { name: 'Test User' },
    logout: jest.fn(),
  }),
}));

describe('Layout component accessibility', () => {
  test('renders mobile navigation with proper ARIA attributes and focus styles', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout />
      </MemoryRouter>
    );

    const mobileNav = screen.getByRole('navigation', { name: 'Mobile navigation' });
    expect(mobileNav).toBeInTheDocument();

    const meetingsLink = within(mobileNav).getByRole('link', { name: 'Meetings dashboard' });
    expect(meetingsLink).toBeInTheDocument();
    expect(meetingsLink.className).toContain('focus-visible:ring-2');

    const logoutBtn = within(mobileNav).getByRole('button', { name: 'Log out' });
    expect(logoutBtn).toBeInTheDocument();
    expect(logoutBtn.className).toContain('focus-visible:ring-2');
  });
});
