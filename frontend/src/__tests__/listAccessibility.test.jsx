import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';
import Settings from '../pages/Settings';
import { AuthProvider } from '../context/AuthContext';
import { meetingService, calendarService, authService } from '../services/api';

jest.mock('../services/api', () => ({
  authService: {
    getCurrentUser: jest.fn(),
  },
  meetingService: {
    getMeetings: jest.fn(),
    processVoiceCommand: jest.fn(),
  },
  calendarService: {
    getEvents: jest.fn(),
  },
  default: {
    get: jest.fn().mockResolvedValue({ data: { success: false } }),
  },
}));

beforeEach(() => {
  jest.clearAllMocks();
  authService.getCurrentUser.mockResolvedValue({
    user: { id: 'u1', name: 'Test User', email: 'user@example.com' },
  });
});

describe('Semantic list structure and icon accessibility', () => {
  test('Dashboard renders scheduled meetings in a semantic list container with aria-label', async () => {
    meetingService.getMeetings.mockResolvedValue({
      meetings: [
        { id: 'm1', title: 'Team Sync', start_time: '2026-09-01T10:00:00Z', duration: 30 },
        { id: 'm2', title: 'Product Review', start_time: '2026-09-01T14:00:00Z', duration: 45 },
      ],
    });

    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText('Team Sync')).toBeInTheDocument());

    const list = screen.getByRole('list', { name: 'Scheduled meetings' });
    expect(list).toBeInTheDocument();

    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(2);

    // Decorative SVG icons within list should have aria-hidden="true"
    const svgs = list.querySelectorAll('svg');
    svgs.forEach((svg) => {
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });

  test('Settings renders synced calendar events in a semantic list container with aria-label', async () => {
    calendarService.getEvents.mockResolvedValue({
      events: [
        { id: 'e1', title: 'Google Calendar Standup', start: '2026-09-01T10:00:00Z' },
      ],
    });

    render(
      <AuthProvider>
        <Settings />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('Google Calendar Standup')).toBeInTheDocument());

    const list = screen.getByRole('list', { name: 'Synced calendar events' });
    expect(list).toBeInTheDocument();

    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(1);

    const svgs = list.querySelectorAll('svg');
    svgs.forEach((svg) => {
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });
});
