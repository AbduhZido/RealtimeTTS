import { describe, it, expect } from 'vitest';
import { float32ToInt16, resampleAudio } from '@/audio';

describe('Audio Utilities', () => {
  describe('float32ToInt16', () => {
    it('should convert float32 samples to int16', () => {
      const float32 = new Float32Array([0, 0.5, 1, -0.5, -1]);
      const int16 = float32ToInt16(float32);

      expect(int16).toBeInstanceOf(Uint8Array);
      expect(int16.length).toBe(float32.length * 2);
    });

    it('should clamp float values to [-1, 1]', () => {
      const float32 = new Float32Array([2, -2, 0.5]);
      const int16 = float32ToInt16(float32);

      expect(int16).toBeInstanceOf(Uint8Array);
    });

    it('should handle zero samples', () => {
      const float32 = new Float32Array([0, 0, 0, 0]);
      const int16 = float32ToInt16(float32);

      expect(int16.length).toBe(8);
    });
  });

  describe('resampleAudio', () => {
    it('should return same data when sample rates match', () => {
      const original = new Float32Array([0, 0.5, 1]);
      const resampled = resampleAudio(original, 16000, 16000);

      expect(resampled).toBe(original);
    });

    it('should downsample audio correctly', () => {
      const original = new Float32Array([0, 0.25, 0.5, 0.75, 1]);
      const resampled = resampleAudio(original, 48000, 16000);

      expect(resampled.length).toBeLessThan(original.length);
    });

    it('should upsample audio correctly', () => {
      const original = new Float32Array([0, 0.5, 1]);
      const resampled = resampleAudio(original, 8000, 16000);

      expect(resampled.length).toBeGreaterThan(original.length);
    });
  });
});
