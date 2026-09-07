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

  test('renders skip to main content link targeting main content area', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout />
      </MemoryRouter>
    );

    const skipLink = screen.getByRole('link', { name: 'Skip to main content' });
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute('href', '#main-content');

    const mainElement = screen.getByRole('main');
    expect(mainElement).toHaveAttribute('id', 'main-content');
    expect(mainElement).toHaveAttribute('tabIndex', '-1');
  });
});
