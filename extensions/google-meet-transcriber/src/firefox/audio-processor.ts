import browser from 'webextension-polyfill';

class AudioProcessor {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;

  async initialize(stream: MediaStream): Promise<void> {
    this.mediaStream = stream;
    const AudioContext = window.AudioContext || (window as Record<string, unknown>).webkitAudioContext as typeof window.AudioContext;
    this.audioContext = new AudioContext();
    
    const source = this.audioContext.createMediaStreamSource(stream);
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);

    this.processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const audioBytes = this.float32ToInt16(inputData);
      
      browser.runtime.sendMessage({
        type: 'audioData',
        data: btoa(String.fromCharCode.apply(null, Array.from(audioBytes))),
      }).catch(() => {});
    };
  }

  private float32ToInt16(float32Data: Float32Array): Uint8Array {
    const int16Data = new Int16Array(float32Data.length);
    
    for (let i = 0; i < float32Data.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Data[i]));
      int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    return new Uint8Array(int16Data.buffer);
  }

  stop(): void {
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}

const processor = new AudioProcessor();

browser.runtime.onMessage.addListener(async (request: unknown) => {
  const msg = request as Record<string, unknown>;
  if (msg.type === 'initAudioProcessor' && msg.stream instanceof MediaStream) {
    await processor.initialize(msg.stream);
  } else if (msg.type === 'stopAudioProcessor') {
    processor.stop();
  }
});
