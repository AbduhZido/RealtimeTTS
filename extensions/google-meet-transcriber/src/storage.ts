import browser from 'webextension-polyfill';
import { TranscriptionConfig } from '@/types';

const DEFAULT_CONFIG: TranscriptionConfig = {
  backendUrl: 'ws://localhost:8000/ws/transcribe',
  language: 'en-US',
};

export async function loadConfig(): Promise<TranscriptionConfig> {
  const result = await browser.storage.sync.get('transcriptionConfig');
  return result.transcriptionConfig || DEFAULT_CONFIG;
}

export async function saveConfig(config: Partial<TranscriptionConfig>): Promise<void> {
  const current = await loadConfig();
  const updated = { ...current, ...config };
  await browser.storage.sync.set({ transcriptionConfig: updated });
}

export async function resetConfig(): Promise<void> {
  await browser.storage.sync.remove('transcriptionConfig');
}

export async function getTranscriptHistory(): Promise<string> {
  const result = await browser.storage.local.get('transcriptHistory');
  return result.transcriptHistory || '';
}

export async function saveTranscriptHistory(transcript: string): Promise<void> {
  const current = await getTranscriptHistory();
  const updated = current + (current ? '\n' : '') + transcript;
  await browser.storage.local.set({ transcriptHistory: updated });
}

export async function clearTranscriptHistory(): Promise<void> {
  await browser.storage.local.remove('transcriptHistory');
}
