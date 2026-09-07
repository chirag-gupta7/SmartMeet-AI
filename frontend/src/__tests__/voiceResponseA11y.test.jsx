import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import VoiceInput from '../components/VoiceInput';
import Dashboard from '../pages/Dashboard';

jest.mock('../services/api', () => ({
  meetingService: {
    getMeetings: jest.fn().mockResolvedValue({ meetings: [] }),
    processVoiceCommand: jest.fn(),
  },
  default: {
    get: jest.fn().mockResolvedValue({ data: { success: false } }),
  },
}));

jest.mock('../components/VoiceInput', () => {
  const React = require('react');
  return function DummyVoiceInput({ onTranscript, responseMessage }) {
    return (
      <div data-testid="voice-input-mock">
        {responseMessage && (
          <div role="status" aria-live="polite" data-testid="response-msg">
            {responseMessage}
          </div>
        )}
        <button
          type="button"
          onClick={() => onTranscript('Schedule sync')}
        >
          Send Voice Transcript
        </button>
      </div>
    );
  };
});

import { meetingService } from '../services/api';

describe('Voice command feedback accessibility and error recovery', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('VoiceInput response message container has role="status" and aria-live="polite"', () => {
    // Unmock VoiceInput for unit test of VoiceInput itself
    const ActualVoiceInput = jest.requireActual('../components/VoiceInput').default;

    render(
      <ActualVoiceInput
        onTranscript={jest.fn()}
        onProcessing={jest.fn()}
        responseMessage="Meeting scheduled for 2 PM"
        authUrl={null}
      />
    );

    const statusContainer = screen.getByRole('status');
    expect(statusContainer).toBeInTheDocument();
    expect(statusContainer).toHaveAttribute('aria-live', 'polite');
    expect(statusContainer).toHaveTextContent('Meeting scheduled for 2 PM');
  });

  test('Dashboard shows role="status" processing indicator and handles command errors gracefully', async () => {
    meetingService.processVoiceCommand.mockRejectedValueOnce(
      new Error('Network error processing voice command')
    );

    render(<Dashboard />);

    // Open voice scheduler panel
    const toggleBtn = screen.getByRole('button', { name: /schedule a meeting/i });
    fireEvent.click(toggleBtn);

    // Trigger transcript
    const sendBtn = screen.getByText('Send Voice Transcript');
    fireEvent.click(sendBtn);

    // Verify error message was displayed in responseMessage container
    await waitFor(() => {
      const responseEl = screen.getByTestId('response-msg');
      expect(responseEl).toBeInTheDocument();
      expect(responseEl).toHaveTextContent('Failed to process voice command. Please try again.');
      expect(responseEl).toHaveAttribute('role', 'status');
      expect(responseEl).toHaveAttribute('aria-live', 'polite');
    });
  });
});
