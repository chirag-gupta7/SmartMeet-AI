import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

jest.mock('../services/api', () => ({
  authService: {
    googleLogin: jest.fn(),
    login: jest.fn(),
    register: jest.fn(),
    getCurrentUser: jest.fn(),
  },
  meetingService: {},
  calendarService: { getEvents: jest.fn(), sync: jest.fn() },
  default: {},
}));

import { authService, calendarService } from '../services/api';
import { AuthProvider } from '../context/AuthContext';
import Settings from '../pages/Settings';

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  authService.getCurrentUser.mockResolvedValue({
    user: { id: 'u1', name: 'Test', email: 't@example.com' },
  });
});

function renderSettings() {
  return render(
    <AuthProvider>
      <Settings />
    </AuthProvider>
  );
}

describe('Settings calendar panel regression (M2/D3)', () => {
  test('renders events using the start field without Invalid Date', async () => {
    calendarService.getEvents.mockResolvedValue({
      source: 'google',
      events: [
        { id: 'e1', title: 'Standup', start: '2026-09-01T10:00:00Z', source: 'google' },
      ],
    });

    renderSettings();

    await waitFor(() => expect(screen.getByText('Standup')).toBeInTheDocument());
    expect(screen.queryByText(/Invalid Date/i)).not.toBeInTheDocument();
  });

  test('"Sync now" refreshes the event list instead of calling the dead sync endpoint', async () => {
    calendarService.getEvents
      .mockResolvedValueOnce({ source: 'local', events: [] })
      .mockResolvedValueOnce({
        source: 'local',
        events: [{ id: 'e2', title: 'Review', start: '2026-09-02T09:00:00Z' }],
      });

    renderSettings();
    await waitFor(() =>
      expect(calendarService.getEvents).toHaveBeenCalledTimes(1)
    );

    fireEvent.click(screen.getByText('Sync now'));

    await waitFor(() =>
      expect(calendarService.getEvents).toHaveBeenCalledTimes(2)
    );
    expect(await screen.findByText('Calendar refreshed.')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Review')).toBeInTheDocument());

    // The always-failing bare POST /calendar/sync must not be used.
    expect(calendarService.sync).not.toHaveBeenCalled();
  });
});
