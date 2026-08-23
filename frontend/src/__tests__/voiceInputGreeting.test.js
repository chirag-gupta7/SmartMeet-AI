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
    // Never-resolving promise keeps the component in its listening state.
    startListening: jest.fn(() => new Promise(() => {})),
    stopListening: jest.fn(),
  },
}));

import api from '../services/api';
import { voiceService } from '../services/voiceService';
import VoiceInput from '../components/VoiceInput';

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  localStorage.setItem('token', 'tok-1');
  // CRA's resetMocks wipes factory implementations, so set them per test.
  voiceService.isSupported.mockReturnValue(true);
});

describe('VoiceInput greeting fetch regression (M3)', () => {
  test('greeting is fetched through the shared axios instance (API baseURL)', async () => {
    // success:false skips the audio path; we only assert the request target.
    api.get.mockResolvedValue({ data: { success: false } });

    render(
      <VoiceInput onTranscript={jest.fn()} onProcessing={jest.fn()} responseMessage="" authUrl={null} />
    );

    const button = await screen.findByRole('button');
    expect(button).not.toBeDisabled();

    fireEvent.click(button);

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/voice/greeting')
    );
  });
});
