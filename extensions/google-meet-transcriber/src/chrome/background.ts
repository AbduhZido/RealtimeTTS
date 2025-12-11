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
let captureStreamId: string | null = null;

browser.runtime.onMessage.addListener(
  async (request: unknown, sender) => {
    const msg = request as Record<string, unknown>;
    
    if (msg.type === 'startTranscription') {
      return handleStartTranscription(sender.tab?.id);
    } else if (msg.type === 'stopTranscription') {
      return handleStopTranscription();
    } else if (msg.type === 'getState') {
      return Promise.resolve(state);
    }
  }
);

async function handleStartTranscription(tabId?: number): Promise<StorageState> {
  if (state.isTranscribing) {
    return state;
  }

  if (!tabId) {
    state.error = 'No active tab found';
    return state;
  }

  try {
    const config = await loadConfig();
    const stream = await browser.tabCapture.capture({
      audio: true,
      video: false,
    });

    if (!stream) {
      state.error = 'Failed to capture tab audio';
      return state;
    }

    captureStreamId = stream.id;
    state.activeTabId = tabId;
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

    const mediaStream = new MediaStream();
    const audioTracks = stream.getAudioTracks();
    audioTracks.forEach((track) => mediaStream.addTrack(track));

    const AudioContext = window.AudioContext || (window as Record<string, unknown>).webkitAudioContext as typeof window.AudioContext;
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(mediaStream);

    await initializeAudioProcessing(
      source,
      audioContext,
      wsClient,
      tabId
    );

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

    if (captureStreamId) {
      await browser.tabCapture.stopCapture(captureStreamId);
      captureStreamId = null;
    }

    state.isTranscribing = false;
    state.sessionId = undefined;

    return state;
  } catch (error) {
    state.error = error instanceof Error ? error.message : 'Unknown error';
    return state;
  }
}

async function initializeAudioProcessing(
  source: MediaStreamAudioSourceNode,
  audioContext: AudioContext,
  wsClient: WebSocketClient,
  _tabId: number
): Promise<void> {
  try {
    const offscreenUrl = browser.runtime.getURL('chrome/offscreen.html');
    await browser.offscreen.createDocument({
      url: offscreenUrl,
      reasons: ['WEB_ACCESSIBLE_RESOURCES'],
    });

    browser.runtime.onMessage.addListener((request: unknown) => {
      const msg = request as Record<string, unknown>;
      if (msg.type === 'audioData' && typeof msg.data === 'string') {
        const audioData = new Uint8Array(
          atob(msg.data)
            .split('')
            .map((c) => c.charCodeAt(0))
        );
        wsClient.sendAudio(audioData);
      }
    });

    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    source.connect(processor);
    processor.connect(audioContext.destination);

    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const audioBytes = float32ToInt16(inputData);
      wsClient.sendAudio(audioBytes);
    };
  } catch (error) {
    console.error('Failed to initialize audio processing:', error);
  }
}

function float32ToInt16(float32Data: Float32Array): Uint8Array {
  const int16Data = new Int16Array(float32Data.length);
  
  for (let i = 0; i < float32Data.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Data[i]));
    int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }

  return new Uint8Array(int16Data.buffer);
}

browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && state.activeTabId === tabId) {
    const isMeetUrl = tab.url?.includes('meet.google.com');
    if (!isMeetUrl && state.isTranscribing) {
      handleStopTranscription();
    }
  }
});

browser.tabs.onRemoved.addListener((tabId) => {
  if (state.activeTabId === tabId && state.isTranscribing) {
    handleStopTranscription();
  }
});
