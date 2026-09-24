import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';
import { meetingService } from '../services/api';

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
  return function MockVoiceInput({ onTranscript }) {
    return (
      <div data-testid="mock-voice-input">
        <button
          type="button"
          onClick={() => onTranscript('Schedule test meeting')}
          data-testid="simulate-transcript-btn"
        >
          Submit Transcript
        </button>
      </div>
    );
  };
});

describe('Dashboard voice scheduler toggle ARIA attributes', () => {
  beforeEach(() => {
    meetingService.getMeetings.mockResolvedValue({ meetings: [] });
    meetingService.processVoiceCommand.mockResolvedValue({ success: true, message: 'Done' });
  });

  test('toggle button updates aria-expanded and controls voice-scheduler-panel', async () => {
    render(<Dashboard />);

    const toggleBtn = screen.getByRole('button', { name: /schedule a meeting/i });
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

  test('empty state button has aria-expanded and aria-controls attributes', async () => {
    render(<Dashboard />);

    const emptyStateBtn = screen.getByRole('button', { name: /schedule your first meeting/i });
    expect(emptyStateBtn).toHaveAttribute('aria-expanded', 'false');
    expect(emptyStateBtn).toHaveAttribute('aria-controls', 'voice-scheduler-panel');

    fireEvent.click(emptyStateBtn);

    const panel = document.getElementById('voice-scheduler-panel');
    expect(panel).toBeInTheDocument();
  });

  test('displays dismissible success banner with role="status" on successful voice command', async () => {
    render(<Dashboard />);

    // Open voice scheduler
    fireEvent.click(screen.getByRole('button', { name: /schedule a meeting/i }));

    // Click mock voice input trigger to fire transcript
    fireEvent.click(screen.getByTestId('simulate-transcript-btn'));

    // Verify success banner with text 'Done' and role="status" is displayed
    const bannerText = await screen.findByText('Done');
    expect(bannerText).toBeInTheDocument();
    const statusContainer = bannerText.closest('[role="status"]');
    expect(statusContainer).toBeInTheDocument();

    // Dismiss the success banner
    const dismissBtn = screen.getByRole('button', { name: /dismiss message/i });
    fireEvent.click(dismissBtn);

    expect(screen.queryByText('Done')).not.toBeInTheDocument();
  });
});
