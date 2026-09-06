import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

jest.mock('../services/api', () => ({
  __esModule: true,
  default: { get: jest.fn() },
  authService: { getCurrentUser: jest.fn() },
  meetingService: {},
  calendarService: {},
}));

jest.mock('../services/voiceService', () => ({
  voiceService: {
    isSupported: jest.fn(() => true),
    startListening: jest.fn(),
    stopListening: jest.fn(),
  },
}));

import api from '../services/api';
import { voiceService } from '../services/voiceService';
import VoiceInput from '../components/VoiceInput';

beforeEach(() => {
  jest.clearAllMocks();
  voiceService.isSupported.mockReturnValue(true);
});

describe('VoiceInput error recovery & dismissal', () => {
  test('displays dismiss button on transient error and clears error when clicked', async () => {
    api.get.mockResolvedValue({ data: { success: false } });
    voiceService.startListening.mockRejectedValue(new Error('Microphone access denied'));

    render(
      <VoiceInput onTranscript={jest.fn()} onProcessing={jest.fn()} responseMessage="" authUrl={null} />
    );

    const button = screen.getByRole('button', { name: 'Start voice assistant' });
    fireEvent.click(button);

    const errorAlert = await screen.findByRole('alert');
    expect(errorAlert).toHaveTextContent('Microphone access denied');

    const dismissButton = screen.getByRole('button', { name: 'Dismiss error' });
    expect(dismissButton).toBeInTheDocument();

    fireEvent.click(dismissButton);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  test('button remains enabled on transient error so user can retry', async () => {
    api.get.mockResolvedValue({ data: { success: false } });
    voiceService.startListening.mockRejectedValue(new Error('Speech recognition timeout'));

    render(
      <VoiceInput onTranscript={jest.fn()} onProcessing={jest.fn()} responseMessage="" authUrl={null} />
    );

    const button = screen.getByRole('button', { name: 'Start voice assistant' });
    fireEvent.click(button);

    await screen.findByRole('alert');

    // The mic button should NOT be disabled when browser is supported
    expect(button).not.toBeDisabled();
  });
});
