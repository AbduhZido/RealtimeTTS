// Options page script
const DEFAULT_RELAY_URL = 'ws://localhost:8000';
const DEFAULT_LANGUAGE = 'en';

document.addEventListener('DOMContentLoaded', loadSettings);

document.getElementById('save').addEventListener('click', saveSettings);
document.getElementById('reset').addEventListener('click', resetSettings);

function loadSettings() {
  chrome.storage.sync.get(['relayUrl', 'language'], (data) => {
    document.getElementById('relayUrl').value = data.relayUrl || DEFAULT_RELAY_URL;
    document.getElementById('language').value = data.language || DEFAULT_LANGUAGE;
  });
}

function saveSettings() {
  const relayUrl = document.getElementById('relayUrl').value.trim();
  const language = document.getElementById('language').value;

  if (!relayUrl) {
    showStatus('Please enter a relay URL', 'error');
    return;
  }

  chrome.storage.sync.set({ relayUrl, language }, () => {
    showStatus('Settings saved successfully', 'success');
    setTimeout(() => hideStatus(), 2000);
  });
}

function resetSettings() {
  document.getElementById('relayUrl').value = DEFAULT_RELAY_URL;
  document.getElementById('language').value = DEFAULT_LANGUAGE;

  chrome.storage.sync.set(
    {
      relayUrl: DEFAULT_RELAY_URL,
      language: DEFAULT_LANGUAGE,
    },
    () => {
      showStatus('Settings reset to defaults', 'success');
      setTimeout(() => hideStatus(), 2000);
    }
  );
}

function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = 'status ' + type;
}

function hideStatus() {
  const statusDiv = document.getElementById('status');
  statusDiv.className = 'status';
}
