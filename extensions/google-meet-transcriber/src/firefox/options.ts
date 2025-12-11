import { loadConfig, saveConfig } from '@/storage';

const form = document.getElementById('settingsForm') as HTMLFormElement;
const backendUrlInput = document.getElementById('backendUrl') as HTMLInputElement;
const apiKeyInput = document.getElementById('apiKey') as HTMLInputElement;
const languageInput = document.getElementById('language') as HTMLInputElement;
const webhookIdsInput = document.getElementById('webhookIds') as HTMLTextAreaElement;
const successMessage = document.getElementById('successMessage') as HTMLDivElement;

async function loadSettings(): Promise<void> {
  const config = await loadConfig();
  backendUrlInput.value = config.backendUrl;
  apiKeyInput.value = config.apiKey || '';
  languageInput.value = config.language;
  webhookIdsInput.value = (config.webhookIds || []).join('\n');
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const webhookIds = webhookIdsInput.value
    .split('\n')
    .map((id) => id.trim())
    .filter((id) => id.length > 0);

  await saveConfig({
    backendUrl: backendUrlInput.value,
    apiKey: apiKeyInput.value || undefined,
    language: languageInput.value,
    webhookIds: webhookIds.length > 0 ? webhookIds : undefined,
  });

  successMessage.classList.add('show');
  setTimeout(() => {
    successMessage.classList.remove('show');
  }, 2000);
});

loadSettings();
