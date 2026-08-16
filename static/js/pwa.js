if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
  });
}

let deferredInstallPrompt = null;

window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredInstallPrompt = e;
  const btn = document.getElementById('btn-install');
  if (btn) btn.classList.remove('hidden');
});

window.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btn-install');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    btn.classList.add('hidden');
    if (typeof closeMenuDropdown === 'function') closeMenuDropdown();
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
  });
});

window.addEventListener('appinstalled', () => {
  const btn = document.getElementById('btn-install');
  if (btn) btn.classList.add('hidden');
  deferredInstallPrompt = null;
});
