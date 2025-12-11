# Google Meet Transcriber Extension

A Chrome and Firefox extension that captures Google Meet audio and streams it to the RealtimeTTS meet_transcriber relay service for real-time transcription.

## Features

- **Real-time Audio Capture**: Captures audio from active Google Meet tabs
- **WebSocket Streaming**: Streams audio frames (16kHz PCM Int16) to the relay service
- **Start/Stop Toggle**: Simple in-call UI for controlling transcription
- **Configuration**: Customize backend URL, API key, language, and webhook IDs
- **Status Monitoring**: Visual indicators for recording status and errors
- **Transcript Preview**: Display live transcript snippets in the popup

## Installation

### Chrome

1. **Build the extension**:
   ```bash
   npm install
   npm run build
   ```

2. **Load unpacked**:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `dist/chrome` directory

### Firefox

1. **Build the extension**:
   ```bash
   npm install
   npm run build
   ```

2. **Load temporary add-on**:
   - Open `about:debugging#/runtime/this-firefox`
   - Click "Load Temporary Add-on"
   - Select the `dist/firefox/manifest.json` file

## Configuration

1. Click the extension icon in the toolbar
2. Click the ⚙️ settings button
3. Configure:
   - **Backend URL**: WebSocket URL of your meet_transcriber service (e.g., `ws://localhost:8000/ws/transcribe`)
   - **API Key**: Optional authentication token
   - **Language**: Language code (e.g., `en-US`, `es-ES`)
   - **Webhook IDs**: Optional webhook endpoints for results

## Usage

1. Open a Google Meet call
2. Click the extension popup
3. Click "Start" to begin capturing and transcribing
4. The transcript will appear in real-time in the popup
5. Click "Stop" to end the session

## Development

### Project Structure

```
├── src/
│   ├── types.ts                 # TypeScript interfaces
│   ├── storage.ts               # Chrome storage utilities
│   ├── audio.ts                 # Audio processing functions
│   ├── websocket.ts             # WebSocket client
│   ├── chrome/
│   │   ├── manifest.json        # Chrome Manifest V3
│   │   ├── background.ts        # Service worker
│   │   ├── content.ts           # Content script
│   │   ├── popup.html/ts        # Popup UI
│   │   └── options.html/ts      # Settings page
│   ├── firefox/
│   │   ├── manifest.json        # Firefox Manifest V2
│   │   ├── background.ts        # Background script
│   │   ├── content.ts           # Content script
│   │   ├── popup.html/ts        # Popup UI
│   │   └── options.html/ts      # Settings page
│   └── __tests__/               # Test files
├── vite.config.ts              # Build configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies
└── README.md                   # This file
```

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for both Chrome and Firefox
- `npm run lint` - Lint TypeScript code
- `npm test` - Run tests with Vitest
- `npm run pack:chrome` - Build and zip for Chrome
- `npm run pack:firefox` - Build and zip for Firefox

### Build Output

Built files are placed in:
- `dist/chrome/` - Chrome extension
- `dist/firefox/` - Firefox extension

### Testing

Run the test suite:

```bash
npm test
```

Tests cover:
- Audio conversion (float32 to int16)
- Audio resampling
- Storage utilities
- WebSocket client functionality

## WebSocket Protocol

The extension communicates with the relay service using this protocol:

### 1. Init Message (Client → Server)

```json
{
  "type": "init",
  "auth_token": "optional-api-key",
  "participant_info": {
    "extension_version": "0.1.0",
    "browser": "chrome|firefox"
  }
}
```

### 2. Ready Message (Server → Client)

```json
{
  "type": "ready",
  "session_id": "uuid",
  "model": "model-name",
  "language": "en-US"
}
```

### 3. Audio Data (Client → Server)

Binary frames of 16kHz PCM Int16 audio

### 4. Transcript Message (Server → Client)

```json
{
  "type": "transcript",
  "text": "Transcribed text",
  "is_final": true,
  "session_id": "uuid"
}
```

### 5. Stop Message (Client → Server)

```json
{
  "type": "stop"
}
```

## Audio Processing

The extension converts captured audio to 16kHz PCM Int16 format:

1. Capture audio from the tab using `tabCapture` (Chrome) or `getDisplayMedia` (Firefox)
2. Create an `AudioContext` and `ScriptProcessorNode`
3. Convert float32 samples to int16
4. Send frames over WebSocket

## Permissions

### Chrome

- `tabCapture` - Capture audio from tabs
- `storage` - Save user preferences
- `scripting` - Inject content scripts
- `activeTab` - Access current tab

### Firefox

- `tabs` - Access tab information
- `storage` - Save user preferences
- Host permission for `https://meet.google.com/*`

## Browser Compatibility

- **Chrome**: Version 90+
- **Firefox**: Version 91+ (Nightly)

## Troubleshooting

### "No active Google Meet tab found"

- Ensure a Google Meet tab is open in the current window
- Reload the page if needed

### "WebSocket connection error"

- Verify the backend URL is correct
- Check that the meet_transcriber service is running
- Verify network connectivity

### No audio captured

- Check browser permissions for audio capture
- Ensure audio is enabled in the Meet settings
- Try reloading the page

## License

See the main repository LICENSE file.

## Contributing

Contributions are welcome! Please ensure code passes linting and tests before submitting PRs.
