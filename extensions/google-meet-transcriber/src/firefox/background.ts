import browser from 'webextension-polyfill';
import { loadConfig, saveTranscriptHistory } from '@/storage';
import { WebSocketClient } from '@/websocket';
import { TranscriptionState } from '@/types';

interface StorageState extends TranscriptionState {
  activeTabId?: number;
}

const state: StorageState = {
  isTranscribing: false,
  transcript: '',
};

let wsClient: WebSocketClient | null = null;

browser.runtime.onMessage.addListener(
  async (request: unknown) => {
    const msg = request as Record<string, unknown>;
    
    if (msg.type === 'startTranscription') {
      return handleStartTranscription();
    } else if (msg.type === 'stopTranscription') {
      return handleStopTranscription();
    } else if (msg.type === 'getState') {
      return Promise.resolve(state);
    }
  }
);

async function handleStartTranscription(): Promise<StorageState> {
  if (state.isTranscribing) {
    return state;
  }

  try {
    const config = await loadConfig();
    const tabs = await browser.tabs.query({
      url: 'https://meet.google.com/*',
      active: true,
      currentWindow: true,
    });

    if (!tabs.length) {
      state.error = 'No active Google Meet tab found';
      return state;
    }

    const tab = tabs[0];
    state.activeTabId = tab.id;
    state.isTranscribing = true;
    state.error = undefined;
    state.transcript = '';

    wsClient = new WebSocketClient({
      backendUrl: config.backendUrl,
      authToken: config.apiKey,
      onMessage: (message) => {
        if (message.type === 'ready') {
          state.sessionId = message.session_id;
        } else if (message.type === 'transcript') {
          state.transcript += (state.transcript ? ' ' : '') + message.text;
          if (message.is_final) {
            saveTranscriptHistory(message.text);
          }
        } else if (message.type === 'error') {
          state.error = message.message;
        }
      },
      onError: (error) => {
        state.error = error;
        state.isTranscribing = false;
      },
      onClose: () => {
        state.isTranscribing = false;
      },
    });

    await wsClient.connect();

    browser.tabs.sendMessage(tab.id!, {
      type: 'initAudioCapture',
      wsClient: wsClient,
    }).catch(() => {});

    return state;
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Unknown error';
    state.isTranscribing = false;
    return state;
  }
}

async function handleStopTranscription(): Promise<StorageState> {
  if (!state.isTranscribing) {
    return state;
  }

  try {
    if (wsClient) {
      wsClient.stop();
      wsClient = null;
    }

    state.isTranscribing = false;
    state.sessionId = undefined;

    return state;
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Unknown error';
    return state;
  }
}

browser.tabs.onRemoved.addListener((tabId) => {
  if (state.activeTabId === tabId && state.isTranscribing) {
    handleStopTranscription();
  }
});
