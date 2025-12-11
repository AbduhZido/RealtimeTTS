// Content script for Google Meet transcription UI
let isRecording = false;
let uiContainer = null;

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeUI);
} else {
  initializeUI();
}

function initializeUI() {
  // Create UI container
  uiContainer = document.createElement('div');
  uiContainer.id = 'meet-transcriber-container';
  uiContainer.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-width: 280px;
  `;

  // Title
  const title = document.createElement('div');
  title.style.cssText = `
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 12px;
    color: #202124;
  `;
  title.textContent = 'Meet Transcriber';
  uiContainer.appendChild(title);

  // Status indicator
  const statusDiv = document.createElement('div');
  statusDiv.id = 'meet-transcriber-status';
  statusDiv.style.cssText = `
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 13px;
    color: #666;
  `;

  const statusLight = document.createElement('div');
  statusLight.id = 'meet-transcriber-light';
  statusLight.style.cssText = `
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #9e9e9e;
  `;
  statusDiv.appendChild(statusLight);

  const statusText = document.createElement('span');
  statusText.id = 'meet-transcriber-status-text';
  statusText.textContent = 'Idle';
  statusDiv.appendChild(statusText);

  uiContainer.appendChild(statusDiv);

  // Start/Stop button
  const button = document.createElement('button');
  button.id = 'meet-transcriber-button';
  button.textContent = 'Start Transcription';
  button.style.cssText = `
    width: 100%;
    padding: 10px;
    background: #1f73e6;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  `;

  button.onmouseover = () => {
    if (!isRecording) {
      button.style.background = '#1557b0';
    }
  };

  button.onmouseout = () => {
    if (!isRecording) {
      button.style.background = '#1f73e6';
    }
  };

  button.addEventListener('click', toggleRecording);
  uiContainer.appendChild(button);

  // Transcript display
  const transcriptDiv = document.createElement('div');
  transcriptDiv.id = 'meet-transcriber-transcript';
  transcriptDiv.style.cssText = `
    margin-top: 12px;
    padding: 8px;
    background: #f5f5f5;
    border-radius: 4px;
    max-height: 200px;
    overflow-y: auto;
    font-size: 12px;
    color: #444;
    line-height: 1.4;
  `;
  transcriptDiv.textContent = 'Transcriptions will appear here...';
  uiContainer.appendChild(transcriptDiv);

  document.body.appendChild(uiContainer);
}

function toggleRecording() {
  const button = document.getElementById('meet-transcriber-button');

  if (isRecording) {
    // Stop recording
    chrome.runtime.sendMessage({ action: 'stopCapture' }, (response) => {
      if (response && response.status === 'capture_stopped') {
        isRecording = false;
        updateUI(false);
      }
    });
  } else {
    // Start recording
    chrome.storage.sync.get(['relayUrl', 'language'], (data) => {
      const relayUrl = data.relayUrl || 'ws://localhost:8000';
      const language = data.language || 'en';

      chrome.runtime.sendMessage(
        {
          action: 'startCapture',
          relayUrl,
          language,
        },
        (response) => {
          if (response && response.status === 'capture_started') {
            isRecording = true;
            updateUI(true);
          }
        }
      );
    });
  }
}

function updateUI(recording) {
  const button = document.getElementById('meet-transcriber-button');
  const statusLight = document.getElementById('meet-transcriber-light');
  const statusText = document.getElementById('meet-transcriber-status-text');

  if (recording) {
    button.textContent = 'Stop Transcription';
    button.style.background = '#d33f26';
    statusLight.style.background = '#f44336';
    statusText.textContent = 'Recording';
  } else {
    button.textContent = 'Start Transcription';
    button.style.background = '#1f73e6';
    statusLight.style.background = '#9e9e9e';
    statusText.textContent = 'Idle';
  }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'status') {
    if (request.status === 'recording') {
      isRecording = true;
      updateUI(true);
    } else if (request.status === 'error') {
      updateUI(false);
      showError(request.error || 'Unknown error occurred');
    }
    sendResponse({ received: true });
  } else if (request.action === 'transcript') {
    appendTranscript(request.text, request.is_final);
    sendResponse({ received: true });
  }
});

function appendTranscript(text, isFinal) {
  const transcriptDiv = document.getElementById('meet-transcriber-transcript');

  // Clear placeholder on first transcript
  if (transcriptDiv.textContent === 'Transcriptions will appear here...') {
    transcriptDiv.textContent = '';
  }

  const segmentDiv = document.createElement('div');
  segmentDiv.style.cssText = `
    margin-bottom: 4px;
    padding: 4px;
    background: ${isFinal ? '#e8f5e9' : '#fff3e0'};
    border-left: 2px solid ${isFinal ? '#4caf50' : '#ff9800'};
    padding-left: 8px;
  `;
  segmentDiv.textContent = text;
  transcriptDiv.appendChild(segmentDiv);

  // Auto-scroll to bottom
  transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
}

function showError(errorMsg) {
  const transcriptDiv = document.getElementById('meet-transcriber-transcript');
  const errorDiv = document.createElement('div');
  errorDiv.style.cssText = `
    color: #d32f2f;
    padding: 8px;
    background: #ffebee;
    border-radius: 4px;
  `;
  errorDiv.textContent = 'Error: ' + errorMsg;
  transcriptDiv.appendChild(errorDiv);
}
