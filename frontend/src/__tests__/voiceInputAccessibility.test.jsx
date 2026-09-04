import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import VoiceInput from '../components/VoiceInput';
import { voiceService } from '../services/voiceService';

jest.mock('../services/voiceService', () => ({
  voiceService: {
    isSupported: jest.fn().mockReturnValue(true),
    startListening: jest.fn().mockResolvedValue('Schedule meeting at 3pm'),
    stopListening: jest.fn(),
  },
}));

jest.mock('../services/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn().mockResolvedValue({
      data: { success: true, audio_base64: '' },
    }),
  },
}));

describe('VoiceInput Component Accessibility & ARIA', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    voiceService.isSupported.mockReturnValue(true);
  });

  test('renders initial state with accessible ARIA label and status region', () => {
    render(
      <VoiceInput
        onTranscript={jest.fn()}
        onProcessing={jest.fn()}
        responseMessage=""
        authUrl={null}
      />
    );

    const micButton = screen.getByRole('button', { name: /start voice assistant/i });
    expect(micButton).toBeInTheDocument();

    const statusElement = screen.getByRole('status');
    expect(statusElement).toHaveAttribute('aria-live', 'polite');
    expect(statusElement).toHaveTextContent(/tap to start the assistant/i);
  });

  test('renders response message with role="status" and aria-live="polite"', () => {
    render(
      <VoiceInput
        onTranscript={jest.fn()}
        onProcessing={jest.fn()}
        responseMessage="Meeting scheduled successfully!"
        authUrl={null}
      />
    );

    const statuses = screen.getAllByRole('status');
    const responseMsg = statuses.find((el) =>
      el.textContent.includes('Meeting scheduled successfully!')
    );
    expect(responseMsg).toBeInTheDocument();
    expect(responseMsg).toHaveAttribute('aria-live', 'polite');
  });
});
