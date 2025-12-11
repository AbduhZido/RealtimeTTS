const TARGET_SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4096;

export function resampleAudio(
  pcmData: Float32Array,
  fromSampleRate: number,
  toSampleRate: number = TARGET_SAMPLE_RATE
): Float32Array {
  if (fromSampleRate === toSampleRate) {
    return pcmData;
  }

  const ratio = fromSampleRate / toSampleRate;
  const newLength = Math.ceil(pcmData.length / ratio);
  const result = new Float32Array(newLength);

  for (let i = 0; i < newLength; i++) {
    const index = i * ratio;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const fraction = index - lower;

    if (upper >= pcmData.length) {
      result[i] = pcmData[lower];
    } else {
      result[i] =
        pcmData[lower] * (1 - fraction) + pcmData[upper] * fraction;
    }
  }

  return result;
}

export function float32ToInt16(float32Data: Float32Array): Uint8Array {
  const int16Data = new Int16Array(float32Data.length);
  
  for (let i = 0; i < float32Data.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Data[i]));
    int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }

  return new Uint8Array(int16Data.buffer);
}

export function createAudioProcessor(context: AudioContext): ScriptProcessorNode | AudioWorkletNode | null {
  try {
    return context.createScriptProcessor(BUFFER_SIZE, 1, 1);
  } catch {
    return null;
  }
}

export async function initializeAudioWorklet(
  context: AudioContext,
  workletUrl: string
): Promise<boolean> {
  try {
    await context.audioWorklet.addModule(workletUrl);
    return true;
  } catch {
    return false;
  }
}

export function createAudioWorkletNode(
  context: AudioContext
): AudioWorkletNode | null {
  try {
    return new AudioWorkletNode(context, 'audio-processor');
  } catch {
    return null;
  }
}

export function bytesToPCM(buffer: ArrayBuffer): Float32Array {
  const view = new DataView(buffer);
  const length = buffer.byteLength / 2;
  const result = new Float32Array(length);

  let index = 0;
  let inputIndex = 0;

  while (inputIndex < buffer.byteLength) {
    const s = view.getInt16(inputIndex, true);
    result[index++] = s < 0 ? s / 0x8000 : s / 0x7fff;
    inputIndex += 2;
  }

  return result;
}
