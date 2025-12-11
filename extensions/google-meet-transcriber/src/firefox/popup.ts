import browser from 'webextension-polyfill';

const toggleBtn = document.getElementById('toggleBtn') as HTMLButtonElement;
const clearBtn = document.getElementById('clearBtn') as HTMLButtonElement;
const statusDiv = document.getElementById('status') as HTMLDivElement;
const statusText = document.getElementById('statusText') as HTMLDivElement;
const transcriptDiv = document.getElementById('transcript') as HTMLDivElement;
const settingsLink = document.getElementById('settingsLink') as HTMLAnchorElement;

toggleBtn.addEventListener('click', async () => {
  const state = await browser.runtime.sendMessage({
    type: 'getState',
  });

  if (state.isTranscribing) {
    await browser.runtime.sendMessage({
      type: 'stopTranscription',
    });
  } else {
    await browser.runtime.sendMessage({
      type: 'startTranscription',
    });
  }

  updateUI();
});

clearBtn.addEventListener('click', async () => {
  transcriptDiv.innerHTML = '<span class="empty">Cleared</span>';
  setTimeout(() => updateUI(), 1000);
});

settingsLink.addEventListener('click', () => {
  browser.runtime.openOptionsPage();
  window.close();
});

async function updateUI(): Promise<void> {
  const state = await browser.runtime.sendMessage({
    type: 'getState',
  });

  if (state.isTranscribing) {
    toggleBtn.textContent = 'Stop';
    toggleBtn.classList.add('stop');
    statusDiv.classList.remove('inactive', 'error');
    statusDiv.classList.add('active');
    statusText.textContent = 'Recording...';
  } else {
    toggleBtn.textContent = 'Start';
    toggleBtn.classList.remove('stop');
    statusDiv.classList.remove('active');

    if (state.error) {
      statusDiv.classList.add('error');
      statusDiv.classList.remove('inactive');
      statusText.textContent = `Error: ${state.error}`;
    } else {
      statusDiv.classList.add('inactive');
      statusDiv.classList.remove('error');
      statusText.textContent = 'Not recording';
    }
  }

  if (state.transcript) {
    transcriptDiv.innerHTML = state.transcript;
  } else {
    transcriptDiv.innerHTML = '<span class="empty">No transcript yet</span>';
  }
}

setInterval(updateUI, 500);
updateUI();
