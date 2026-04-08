/**
 * content.js
 * Content script for FakeShield Chrome Extension.
 * Runs on all pages, listens for messages from popup.
 */

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractContent') {
    const content = extractPageContent();
    sendResponse(content);
  }
  return true; // Keep message channel open for async response
});

function extractPageContent() {
  const title = document.title || '';
  
  let text = '';
  
  // Try article tag first
  const article = document.querySelector('article');
  if (article) {
    text = article.innerText;
  }
  
  // Try main content areas
  if (!text || text.length < 100) {
    const main = document.querySelector('main, [role="main"]');
    if (main) text = main.innerText;
  }
  
  // Fallback to paragraphs
  if (!text || text.length < 100) {
    const paragraphs = document.querySelectorAll('p');
    text = Array.from(paragraphs)
      .map(p => p.innerText)
      .filter(t => t.length > 20)
      .join(' ');
  }
  
  return {
    title,
    text: `${title}. ${text}`.trim(),
    url: window.location.href,
    domain: window.location.hostname,
  };
}
