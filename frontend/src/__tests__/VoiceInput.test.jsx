import React from 'react';
import { render, screen } from '@testing-library/react';
import VoiceInput from '../components/VoiceInput';
import { voiceService } from '../services/voiceService';

jest.mock('../services/voiceService', () => ({
  voiceService: {
    isSupported: jest.fn(() => true),
    startListening: jest.fn(),
    stopListening: jest.fn(),
  },
}));

describe('VoiceInput component processing state', () => {
  beforeEach(() => {
    voiceService.isSupported.mockReturnValue(true);
  });

  test('renders spinning loader, updates aria-label, and disables button when isProcessing is true', () => {
    const onTranscript = jest.fn();
    const onProcessing = jest.fn();

    render(
      <VoiceInput
        onTranscript={onTranscript}
        onProcessing={onProcessing}
        isProcessing={true}
      />
    );

    const button = screen.getByRole('button', { name: /Processing voice command/i });
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  test('renders standard mic button and enables interaction when isProcessing is false', () => {
    const onTranscript = jest.fn();
    const onProcessing = jest.fn();

    render(
      <VoiceInput
        onTranscript={onTranscript}
        onProcessing={onProcessing}
        isProcessing={false}
      />
    );

    const button = screen.getByRole('button', { name: /Start voice assistant/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'false');
  });
});
