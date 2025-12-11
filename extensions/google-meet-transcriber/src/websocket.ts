import { InitMessage, WebSocketMessage } from '@/types';

export interface WebSocketClientOptions {
  backendUrl: string;
  authToken?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
  maxRetries?: number;
  retryDelay?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private authToken?: string;
  private onMessage?: (message: WebSocketMessage) => void;
  private onError?: (error: string) => void;
  private onClose?: () => void;
  private maxRetries: number;
  private retryDelay: number;
  private retryCount = 0;
  private heartbeatInterval: number | null = null;
  private sessionId: string | null = null;

  constructor(options: WebSocketClientOptions) {
    this.url = options.backendUrl;
    this.authToken = options.authToken;
    this.onMessage = options.onMessage;
    this.onError = options.onError;
    this.onClose = options.onClose;
    this.maxRetries = options.maxRetries ?? 5;
    this.retryDelay = options.retryDelay ?? 1000;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.ws.binaryType = 'arraybuffer';

        this.ws.onopen = () => {
          const initMessage: InitMessage = {
            type: 'init',
            auth_token: this.authToken,
            participant_info: {
              extension_version: '0.1.0',
              browser:
                /Firefox/.test(navigator.userAgent) ? 'firefox' : 'chrome',
            },
          };
          this.ws!.send(JSON.stringify(initMessage));
          this.startHeartbeat();
          this.retryCount = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data) as WebSocketMessage;
            if (message.type === 'ready' && 'session_id' in message) {
              this.sessionId = message.session_id;
            }
            this.onMessage?.(message);
          } catch {
            console.error('Failed to parse WebSocket message', event.data);
          }
        };

        this.ws.onerror = () => {
          const error = 'WebSocket connection error';
          this.onError?.(error);
          reject(new Error(error));
        };

        this.ws.onclose = () => {
          this.stopHeartbeat();
          if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            const delay = this.retryDelay * Math.pow(2, this.retryCount - 1);
            setTimeout(() => this.connect().catch(() => {}), delay);
          } else {
            this.onClose?.();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  sendAudio(data: Uint8Array): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
      return true;
    }
    return false;
  }

  stop(): void {
    const stopMessage = { type: 'stop' };
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(stopMessage));
    }
    this.disconnect();
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const ping = { type: 'ping' };
        try {
          this.ws.send(JSON.stringify(ping));
        } catch {
          // ignore
        }
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval !== null) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
}
