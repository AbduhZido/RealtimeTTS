# Google Meet Transcriber Extension

A lightweight Chrome extension for capturing Google Meet audio and streaming to the meet_transcriber relay service for real-time transcription.

## Features

- **Real-time audio capture** from Google Meet using the Chrome tabCapture API
- **Live transcription** via WebSocket connection to the relay service
- **Configurable relay URL** and language settings
- **Simple UI** with start/stop button and live transcript display
- **PCM audio streaming** at 16kHz, 16-bit mono format
- **Zero dependencies** - pure JavaScript, no build process required

## Installation

### Loading the Extension in Chrome

1. **Open Chrome Extensions Manager**
   - Go to `chrome://extensions/` in your browser
   - Or use menu: ☰ → More Tools → Extensions

2. **Enable Developer Mode**
   - Toggle "Developer mode" in the top-right corner

3. **Load Unpacked Extension**
   - Click "Load unpacked"
   - Navigate to the `extensions/google-meet-transcriber/` folder
   - Select the folder and click "Open"

The extension should now appear in your extensions list and be ready to use.

### Verifying Installation

- You should see the "Google Meet Transcriber" extension in your extensions list
- Navigate to a Google Meet (https://meet.google.com) and you should see the transcriber UI in the top-right corner

## Usage

### Quick Start

1. **Navigate to Google Meet**
   - Open https://meet.google.com and start/join a meeting

2. **Configure Settings (Optional)**
   - Click the extension icon in Chrome's toolbar
   - Click "Options" to set:
     - **Relay Service URL**: Default is `ws://localhost:8000`
     - **Language**: Choose your preferred language (default: English)

3. **Start Transcription**
   - Look for the "Meet Transcriber" UI box in the top-right of the Meet window
   - Click "Start Transcription" button
   - A red "Recording" indicator will appear
   - Live transcripts will appear in the UI as they're generated

4. **Stop Transcription**
   - Click "Stop Transcription" to end the capture
   - The relay service will complete processing and send final results

## Configuration

### Relay Service URL

The extension connects to the relay service via WebSocket. Default settings:
- URL: `ws://localhost:8000`
- Endpoint: `/ws/transcribe`

To change the URL:
1. Right-click the extension icon
2. Select "Options"
3. Update the "Relay Service URL" field
4. Click "Save Settings"

### Language

Select your preferred transcription language from the options:
- English (en) - default
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Simplified Chinese (zh)
- Japanese (ja)
- Korean (ko)

Settings are saved to `chrome.storage.sync` and persist across browser sessions.

## Troubleshooting

### Extension Not Showing on Google Meet

- Ensure you're on https://meet.google.com (not google.com/meet or other variants)
- Try refreshing the page
- Check that extension is enabled in `chrome://extensions/`

### "Recording" Indicator Not Appearing

- Verify the relay service is running and accessible
- Check that the relay URL in options matches your service URL
- Open Chrome DevTools (F12) and check the Console tab for errors

### No Transcriptions Appearing

**Check Relay Service Connection:**
```bash
# Verify relay service is running
curl http://localhost:8000/healthz

# Expected response:
# {"status":"healthy","active_sessions":X,"max_sessions":Y}
```

**Check Browser Console:**
- Open DevTools (F12)
- Look for WebSocket connection errors
- Verify relay URL matches exactly (including protocol: ws:// or wss://)

### Relay Service Not Accessible

Ensure the meet_transcriber service is running:

```bash
# From project root
pip install -e ".[meet]"
python -m meet_transcriber.main

# Or using docker-compose
cd meet_transcriber
docker-compose up
```

Default service runs on `ws://localhost:8000`

## Architecture

### Files

- **manifest.json** - Extension configuration (Manifest V3)
- **background.js** - Audio capture, Web Audio API processing, WebSocket client
- **content.js** - UI injection and transcript display
- **options.html/js** - Settings management with chrome.storage.sync

### Audio Processing Pipeline

1. `chrome.tabCapture.capture()` - Capture Meet audio stream
2. `Web Audio API` - Resample to 16kHz and convert to PCM 16-bit
3. `ScriptProcessorNode` - Process audio in 4096-sample chunks
4. `WebSocket` - Stream PCM frames as binary to relay service

### WebSocket Protocol

**Initialization:**
```json
{
  "type": "init",
  "language": "en",
  "participant_info": {
    "meeting_id": "auto_generated_id",
    "meeting_title": "page_title"
  }
}
```

**Audio Frames:**
```
Binary frame: Int16Array buffer containing PCM samples
```

**Stop Signal:**
```json
{
  "type": "stop"
}
```

## Performance Notes

- Audio processing uses ScriptProcessorNode (simple but not the most efficient)
- For production use with lower latency, consider AudioWorklet integration
- Typical latency: 200-500ms depending on network and relay service performance
- Memory usage: ~20-50MB typical during active recording

## Limitations

- Chrome only (not Firefox yet)
- Requires HTTP or HTTPS relay service (secure WebSocket - wss:// - for production)
- Audio capture only from the Meet tab (not system audio)
- Single recording session per browser

## Future Improvements

- [ ] AudioWorklet for better performance
- [ ] Firefox support
- [ ] Multi-language UI
- [ ] Transcript export/save
- [ ] Speaker identification
- [ ] Session history
- [ ] WebRTC audio quality monitoring

## Development

### Modifying the Extension

Since this is plain JavaScript, you can edit files directly:

1. Edit any JavaScript file
2. Go to `chrome://extensions/`
3. Click "Reload" on the extension card
4. Refresh your Google Meet tab to see changes

### Adding Features

The codebase is structured for easy extension:

- **Add UI elements**: Modify the `initializeUI()` function in `content.js`
- **Add settings**: Add new fields to `options.html` and update `options.js`
- **Modify audio processing**: Edit `convertToPCM16()` in `background.js`

## Support

For issues or questions:

1. Check the Troubleshooting section above
2. Review Chrome DevTools console for error messages
3. Verify relay service is running and accessible
4. Check extension permissions in `chrome://extensions/` settings

## License

Same license as the RealtimeTTS project
