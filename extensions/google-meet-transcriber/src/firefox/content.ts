import browser from 'webextension-polyfill';
import { WebSocketClient } from '@/websocket';

const INJECTED_CLASS = 'meet-transcriber-injected';
let wsClient: WebSocketClient | null = null;
let audioContext: AudioContext | null = null;

function insertUI(): void {
  if (document.querySelector(`.${INJECTED_CLASS}`)) {
    return;
  }

  const container = document.createElement('div');
  container.className = `${INJECTED_CLASS} meet-transcriber-container`;
  container.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 9999;
    background: white;
    padding: 12px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    font-family: Roboto, sans-serif;
    font-size: 13px;
  `;

  const header = document.createElement('div');
  header.style.cssText = 'margin-bottom: 8px; font-weight: 500;';
  header.textContent = 'Transcriber';
  container.appendChild(header);

  const statusChip = document.createElement('div');
  statusChip.className = 'transcriber-status-chip';
  statusChip.style.cssText = `
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    background: #f0f0f0;
    font-size: 11px;
    margin-bottom: 8px;
    color: #666;
  `;
  statusChip.textContent = 'Inactive';
  container.appendChild(statusChip);

  const buttonContainer = document.createElement('div');
  buttonContainer.style.cssText = 'display: flex; gap: 6px;';

  const toggleButton = document.createElement('button');
  toggleButton.className = 'transcriber-toggle-btn';
  toggleButton.style.cssText = `
    padding: 6px 12px;
    background: #4285f4;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
  `;
  toggleButton.textContent = 'Start';

  const settingsButton = document.createElement('button');
  settingsButton.className = 'transcriber-settings-btn';
  settingsButton.style.cssText = `
    padding: 6px 12px;
    background: #e8e8e8;
    color: #333;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  `;
  settingsButton.textContent = '⚙️';

  toggleButton.addEventListener('click', async () => {
    const state = await browser.runtime.sendMessage({
      type: 'getState',
    });

    if (state.isTranscribing) {
      await browser.runtime.sendMessage({
        type: 'stopTranscription',
      });
      stopAudioCapture();
      toggleButton.textContent = 'Start';
      toggleButton.style.background = '#4285f4';
      statusChip.textContent = 'Inactive';
      statusChip.style.background = '#f0f0f0';
      statusChip.style.color = '#666';
    } else {
      await browser.runtime.sendMessage({
        type: 'startTranscription',
      });
      startAudioCapture();
      toggleButton.textContent = 'Stop';
      toggleButton.style.background = '#d32f2f';
      statusChip.textContent = 'Recording...';
      statusChip.style.background = '#fff3cd';
      statusChip.style.color = '#856404';
    }
  });

  settingsButton.addEventListener('click', () => {
    browser.runtime.openOptionsPage();
  });

  buttonContainer.appendChild(toggleButton);
  buttonContainer.appendChild(settingsButton);
  container.appendChild(buttonContainer);

  const transcriptPreview = document.createElement('div');
  transcriptPreview.className = 'transcriber-preview';
  transcriptPreview.style.cssText = `
    margin-top: 8px;
    padding: 8px;
    background: #f9f9f9;
    border-radius: 4px;
    max-height: 100px;
    overflow-y: auto;
    font-size: 11px;
    color: #333;
    max-width: 300px;
    display: none;
  `;
  transcriptPreview.textContent = 'No transcript yet';
  container.appendChild(transcriptPreview);

  document.body.appendChild(container);

  setInterval(async () => {
    const state = await browser.runtime.sendMessage({
      type: 'getState',
    });

    if (state.isTranscribing) {
      if (toggleButton.textContent !== 'Stop') {
        toggleButton.textContent = 'Stop';
        toggleButton.style.background = '#d32f2f';
        statusChip.textContent = 'Recording...';
        statusChip.style.background = '#fff3cd';
        statusChip.style.color = '#856404';
      }

      if (state.transcript) {
        transcriptPreview.style.display = 'block';
        const preview = state.transcript.substring(0, 150);
        transcriptPreview.textContent = preview + (state.transcript.length > 150 ? '...' : '');
      }
    } else {
      if (toggleButton.textContent !== 'Start') {
        toggleButton.textContent = 'Start';
        toggleButton.style.background = '#4285f4';
        statusChip.textContent = state.error || 'Inactive';
        statusChip.style.background = state.error ? '#ffebee' : '#f0f0f0';
        statusChip.style.color = state.error ? '#c62828' : '#666';
      }
      if (state.error) {
        transcriptPreview.style.display = 'block';
        transcriptPreview.textContent = `Error: ${state.error}`;
      } else {
        transcriptPreview.style.display = 'none';
      }
    }
  }, 500);
}

async function startAudioCapture(): Promise<void> {
  try {
    const AudioContext = window.AudioContext || (window as Record<string, unknown>).webkitAudioContext as typeof window.AudioContext;
    audioContext = new AudioContext();

    const stream = await (navigator.mediaDevices as Record<string, unknown> & typeof navigator.mediaDevices).getDisplayMedia({
      audio: true,
      video: false,
    });

    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    source.connect(processor);
    processor.connect(audioContext.destination);

    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const audioBytes = float32ToInt16(inputData);

      if (wsClient && wsClient.isConnected()) {
        wsClient.sendAudio(audioBytes);
      }
    };
  } catch (error) {
    console.error('Failed to capture audio:', error);
  }
}

function stopAudioCapture(): void {
  if (audioContext) {
    audioContext.close();
    audioContext = null;
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

browser.runtime.onMessage.addListener((request: unknown) => {
  const msg = request as Record<string, unknown>;
  if (msg.type === 'initAudioCapture') {
    wsClient = msg.wsClient as WebSocketClient;
    startAudioCapture();
  }
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', insertUI);
} else {
  insertUI();
}
