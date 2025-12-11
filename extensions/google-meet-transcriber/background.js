// Background service worker for Meet audio capture
let captureStreamId = null;
let mediaStreamTrack = null;
let audioContext = null;
let mediaStreamSource = null;
let scriptProcessor = null;
let isCapturing = false;
let currentWebSocket = null;
let currentTabId = null;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'startCapture') {
    handleStartCapture(sender.tabId, request.relayUrl, request.language);
    sendResponse({ status: 'capture_started' });
  } else if (request.action === 'stopCapture') {
    handleStopCapture();
    sendResponse({ status: 'capture_stopped' });
  } else if (request.action === 'getStatus') {
    sendResponse({ isCapturing });
  }
});

async function handleStartCapture(tabId, relayUrl, language) {
  try {
    currentTabId = tabId;

    // Request tab audio capture
    const stream = await chrome.tabCapture.capture({
      audio: true,
      video: false,
    });

    captureStreamId = stream.id;
    mediaStreamTrack = stream.getTracks()[0];
    isCapturing = true;

    // Initialize Web Audio API
    const audioContextOptions = { sampleRate: 16000 };
    audioContext = new AudioContext(audioContextOptions);

    mediaStreamSource = audioContext.createMediaStreamSource(stream);
    scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);

    mediaStreamSource.connect(scriptProcessor);
    scriptProcessor.connect(audioContext.destination);

    // WebSocket client
    const wsUrl = relayUrl.replace(/^http/, 'ws');
    const ws = new WebSocket(wsUrl + '/ws/transcribe');
    currentWebSocket = ws;

    ws.binaryType = 'arraybuffer';
    let sessionId = null;

    ws.onopen = () => {
      const initMessage = {
        type: 'init',
        language: language,
        participant_info: {
          meeting_id: generateSessionId(),
          meeting_title: 'Google Meet',
        },
      };
      ws.send(JSON.stringify(initMessage));
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'ready') {
            sessionId = msg.session_id;
            chrome.tabs.sendMessage(tabId, {
              action: 'status',
              status: 'recording',
              sessionId,
            }).catch(() => {
              // Tab may have been closed
            });
          } else if (msg.type === 'transcript') {
            chrome.tabs.sendMessage(tabId, {
              action: 'transcript',
              text: msg.text,
              is_final: msg.is_final,
            }).catch(() => {
              // Tab may have been closed
            });
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (currentTabId) {
        chrome.tabs.sendMessage(currentTabId, {
          action: 'status',
          status: 'error',
          error: error.message,
        }).catch(() => {
          // Tab may have been closed
        });
      }
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      if (isCapturing) {
        handleStopCapture();
      }
    };

    // Audio processing
    scriptProcessor.onaudioprocess = (event) => {
      if (!isCapturing || ws.readyState !== WebSocket.OPEN) {
        return;
      }

      const inputData = event.inputBuffer.getChannelData(0);
      const pcmData = convertToPCM16(inputData);
      ws.send(pcmData);
    };
  } catch (error) {
    console.error('Error starting capture:', error);
    isCapturing = false;
    if (tabId) {
      chrome.tabs.sendMessage(tabId, {
        action: 'status',
        status: 'error',
        error: error.message,
      }).catch(() => {
        // Tab may have been closed
      });
    }
  }
}

function handleStopCapture() {
  if (currentWebSocket && currentWebSocket.readyState === WebSocket.OPEN) {
    try {
      currentWebSocket.send(JSON.stringify({ type: 'stop' }));
    } catch (e) {
      console.error('Error sending stop message:', e);
    }
    currentWebSocket.close();
    currentWebSocket = null;
  }

  if (mediaStreamTrack) {
    mediaStreamTrack.stop();
    mediaStreamTrack = null;
  }

  if (scriptProcessor) {
    scriptProcessor.disconnect();
    scriptProcessor = null;
  }

  if (mediaStreamSource) {
    mediaStreamSource.disconnect();
    mediaStreamSource = null;
  }

  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }

  isCapturing = false;
  currentTabId = null;
}

function convertToPCM16(floatArray) {
  const pcmData = new Int16Array(floatArray.length);
  for (let i = 0; i < floatArray.length; i++) {
    const s = Math.max(-1, Math.min(1, floatArray[i]));
    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return pcmData.buffer;
}

function generateSessionId() {
  return 'meet_' + Math.random().toString(36).substr(2, 9);
}
