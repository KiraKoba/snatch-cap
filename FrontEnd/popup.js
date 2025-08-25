document.addEventListener('DOMContentLoaded', () => {
  const editorBtn = document.getElementById('caption-editor-btn');

  editorBtn.addEventListener('click', () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL('editor.html'),
    });
  });

  const downloadBtn = document.getElementById('caption-download-btn');

  downloadBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'downloadCaptions' });
  });
});
