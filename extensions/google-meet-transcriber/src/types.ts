export interface TranscriptionConfig {
  backendUrl: string;
  apiKey?: string;
  language: string;
  webhookIds?: string[];
}

export interface InitMessage {
  type: 'init';
  auth_token?: string;
  participant_info?: {
    extension_version: string;
    browser: string;
  };
}

export interface ReadyMessage {
  type: 'ready';
  session_id: string;
  model: string;
  language: string;
}

export interface TranscriptMessage {
  type: 'transcript';
  text: string;
  is_final: boolean;
  session_id: string;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export interface StopMessage {
  type: 'stop';
}

export type WebSocketMessage = InitMessage | ReadyMessage | TranscriptMessage | ErrorMessage | StopMessage;

export interface AudioFrame {
  timestamp: number;
  data: Uint8Array;
}

export interface TabInfo {
  tabId: number;
  url: string;
}

export interface TranscriptionState {
  isTranscribing: boolean;
  sessionId?: string;
  error?: string;
  transcript: string;
}
