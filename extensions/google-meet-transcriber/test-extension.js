/**
 * Test script for the Google Meet Transcriber extension
 * This demonstrates the WebSocket protocol and audio format expected by the relay service
 * 
 * Note: This is for testing/documentation purposes. The actual extension runs in Chrome.
 * To test the extension in a real scenario:
 * 1. Start the meet_transcriber relay service: python -m meet_transcriber.main
 * 2. Load the extension unpacked in Chrome: chrome://extensions/
 * 3. Navigate to https://meet.google.com and start a recording
 * 4. Check relay logs for connection and audio frame reception
 */

const WebSocket = require('ws');

class ExtensionSimulator {
  constructor(relayUrl = 'ws://localhost:8000') {
    this.relayUrl = relayUrl;
    this.ws = null;
    this.sessionId = null;
  }

  async connect(language = 'en') {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.relayUrl + '/ws/transcribe');

        this.ws.on('open', () => {
          console.log('[Extension] Connected to relay service');

          const initMessage = {
            type: 'init',
            language: language,
            participant_info: {
              meeting_id: this.generateSessionId(),
              meeting_title: 'Test Meeting',
            },
          };

          console.log('[Extension] Sending init message:', initMessage);
          this.ws.send(JSON.stringify(initMessage));
        });

        this.ws.on('message', (data) => {
          if (typeof data === 'string') {
            try {
              const msg = JSON.parse(data);
              console.log('[Extension] Received:', msg.type, msg);

              if (msg.type === 'ready') {
                this.sessionId = msg.session_id;
                console.log(
                  `[Extension] Ready! Session ID: ${this.sessionId}`
                );
                resolve(this.sessionId);
              } else if (msg.type === 'transcript') {
                console.log(
                  `[Extension] Transcript: "${msg.text}" (final: ${msg.is_final})`
                );
              }
            } catch (e) {
              console.error('[Extension] Error parsing message:', e);
            }
          }
        });

        this.ws.on('error', (error) => {
          console.error('[Extension] WebSocket error:', error);
          reject(error);
        });

        this.ws.on('close', () => {
          console.log('[Extension] Disconnected from relay service');
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  sendAudioFrame(pcmBuffer) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(pcmBuffer, { binary: true });
    }
  }

  sendStop() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[Extension] Sending stop message');
      this.ws.send(JSON.stringify({ type: 'stop' }));
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
    }
  }

  generateSessionId() {
    return 'meet_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Generate test PCM audio (sine wave at 440Hz for 1 second)
   * This simulates what the extension would send
   */
  generateTestAudio() {
    const sampleRate = 16000;
    const frequency = 440; // A4 note
    const duration = 1; // 1 second
    const samples = sampleRate * duration;
    const pcmData = new Int16Array(samples);

    for (let i = 0; i < samples; i++) {
      const sample = Math.sin((2 * Math.PI * frequency * i) / sampleRate);
      pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }

    return pcmData.buffer;
  }

  async sendTestAudio(durationMs = 3000) {
    const chunkSize = 4096;
    const totalChunks = Math.ceil((durationMs / 1000) * 16000 / chunkSize);

    console.log(
      `[Extension] Sending test audio (${totalChunks} chunks of ${chunkSize} samples)`
    );

    const fullAudio = this.generateTestAudio();
    const int16Array = new Int16Array(fullAudio);

    for (let i = 0; i < totalChunks; i++) {
      const start = (i * chunkSize) % int16Array.length;
      const chunk = int16Array.slice(
        start,
        Math.min(start + chunkSize, int16Array.length)
      );
      this.sendAudioFrame(chunk.buffer);

      // Send chunks with realistic timing
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    console.log('[Extension] Test audio sent');
  }
}

// Run test if this is the main module
if (require.main === module) {
  (async () => {
    const simulator = new ExtensionSimulator('ws://localhost:8000');

    try {
      console.log('[Test] Starting extension simulator...\n');

      // Connect to relay service
      await simulator.connect('en');

      // Send test audio
      await simulator.sendTestAudio(3000);

      // Wait for transcription
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Stop recording
      simulator.sendStop();

      // Wait for cleanup
      await new Promise((resolve) => setTimeout(resolve, 1000));

      simulator.close();
      console.log('\n[Test] Complete!');
    } catch (error) {
      console.error('[Test] Error:', error.message);
      process.exit(1);
    }
  })();
}

module.exports = ExtensionSimulator;
