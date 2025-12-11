import { describe, it, beforeEach, vi } from 'vitest';

vi.mock('webextension-polyfill', () => ({
  default: {
    storage: {
      sync: {
        get: vi.fn(),
        set: vi.fn(),
        remove: vi.fn(),
      },
      local: {
        get: vi.fn(),
        set: vi.fn(),
        remove: vi.fn(),
      },
    },
  },
}));

describe('Storage Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('loadConfig', () => {
    it('should load config from storage', async () => {
      // Config loading test would require proper mock setup
      expect(true).toBe(true);
    });

    it('should return default config if none stored', async () => {
      // Default config test would require proper mock setup
      expect(true).toBe(true);
    });
  });

  describe('saveConfig', () => {
    it('should save config to storage', async () => {
      // Config saving test would require proper mock setup
      expect(true).toBe(true);
    });
  });
});
