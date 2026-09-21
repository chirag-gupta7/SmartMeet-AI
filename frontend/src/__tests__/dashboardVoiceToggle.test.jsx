import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';

// Mock meetingService API
jest.mock('../services/api', () => ({
  meetingService: {
    getMeetings: jest.fn().mockResolvedValue({ meetings: [] }),
    processVoiceCommand: jest.fn().mockResolvedValue({ success: true, message: 'Done' }),
  },
  default: {
    get: jest.fn().mockResolvedValue({ data: { success: false } }),
  },
}));

// Mock VoiceInput component to simplify test
jest.mock('../components/VoiceInput', () => {
  return function MockVoiceInput() {
    return <div data-testid="mock-voice-input">Voice Input</div>;
  };
});

describe('Dashboard voice scheduler toggle ARIA attributes', () => {
  test('renders loading indicator with role="status" and aria-live="polite" during initial fetch', async () => {
    render(<Dashboard />);
    const statusMsg = screen.getByRole('status');
    expect(statusMsg).toHaveAttribute('aria-live', 'polite');
    expect(statusMsg).toHaveTextContent(/loading meetings/i);
    await screen.findByRole('button', { name: /schedule a meeting/i });
  });

  test('toggle button updates aria-expanded and controls voice-scheduler-panel', async () => {
    render(<Dashboard />);

    const toggleBtn = await screen.findByRole('button', { name: /schedule a meeting/i });
    expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');
    expect(toggleBtn).toHaveAttribute('aria-controls', 'voice-scheduler-panel');

    // Click to open voice scheduler
    fireEvent.click(toggleBtn);

    expect(toggleBtn).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText('Close scheduler')).toBeInTheDocument();

    const panel = document.getElementById('voice-scheduler-panel');
    expect(panel).toBeInTheDocument();

    // Click to close voice scheduler
    fireEvent.click(toggleBtn);

    expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText('Schedule a meeting')).toBeInTheDocument();
  });
});
