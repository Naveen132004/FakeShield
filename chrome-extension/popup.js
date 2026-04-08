/**
 * popup.js
 * Chrome Extension popup logic for FakeShield.
 * Extracts page content, sends to backend, displays results.
 */

const API_BASE = 'http://localhost:8000';

const analyzeBtn = document.getElementById('analyzeBtn');
const status = document.getElementById('status');
const resultContainer = document.getElementById('resultContainer');
const errorContainer = document.getElementById('errorContainer');

analyzeBtn.addEventListener('click', async () => {
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = '⏳ Analyzing...';
  status.textContent = 'Extracting page content...';
  resultContainer.innerHTML = '';
  errorContainer.innerHTML = '';

  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      throw new Error('No active tab found');
    }

    // Extract text from the page using content script
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractPageContent,
    });

    const pageContent = result.result;
    
    if (!pageContent || pageContent.text.length < 20) {
      throw new Error('Could not extract enough text from this page');
    }

    status.textContent = `Analyzing ${pageContent.text.length} characters...`;

    // Send to backend
    const response = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: pageContent.text.substring(0, 10000) }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `API error: ${response.status}`);
    }

    const data = await response.json();
    displayResult(data, tab.url);
    status.textContent = 'Analysis complete!';
    
  } catch (err) {
    errorContainer.innerHTML = `<div class="error">⚠️ ${err.message}</div>`;
    status.textContent = 'Analysis failed';
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = '🔍 Analyze This Page';
  }
});

/**
 * Extracts main content from the current webpage.
 * This function runs in the page context.
 */
function extractPageContent() {
  // Get title
  const title = document.title || '';
  
  // Try to get article content
  let text = '';
  
  // Strategy 1: article tag
  const article = document.querySelector('article');
  if (article) {
    text = article.innerText;
  }
  
  // Strategy 2: main tag
  if (!text || text.length < 100) {
    const main = document.querySelector('main');
    if (main) text = main.innerText;
  }
  
  // Strategy 3: common content selectors
  if (!text || text.length < 100) {
    const selectors = [
      '.article-body', '.article-content', '.post-content',
      '.entry-content', '.story-body', '[role="main"]',
      '.content', '#content'
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText.length > 100) {
        text = el.innerText;
        break;
      }
    }
  }
  
  // Strategy 4: all paragraphs
  if (!text || text.length < 100) {
    const paragraphs = document.querySelectorAll('p');
    text = Array.from(paragraphs)
      .map(p => p.innerText)
      .filter(t => t.length > 20)
      .join(' ');
  }
  
  // Combine title and text
  const fullText = `${title}. ${text}`.trim();
  
  return {
    title,
    text: fullText,
    url: window.location.href,
    domain: window.location.hostname,
  };
}

/**
 * Display analysis results in the popup.
 */
function displayResult(data, url) {
  const isFake = data.prediction === 'FAKE';
  const gaugeColor = data.credibility_score >= 70 ? '#22c55e' : 
                     data.credibility_score >= 50 ? '#f59e0b' : '#ef4444';
  
  let html = `
    <div class="result">
      <div class="verdict ${isFake ? 'fake' : 'real'}">
        <div class="verdict-icon">${isFake ? '🚨' : '✅'}</div>
        <div class="verdict-label ${isFake ? 'fake' : 'real'}">
          ${isFake ? 'LIKELY FAKE' : 'LIKELY REAL'}
        </div>
        <div class="verdict-conf">${data.confidence}% confidence</div>
      </div>
      
      <div class="metrics">
        <div class="metric">
          <div class="metric-val" style="color: ${gaugeColor}">${data.credibility_score}</div>
          <div class="metric-label">Credibility</div>
        </div>
        <div class="metric">
          <div class="metric-val" style="color: #ef4444">${data.fake_probability}%</div>
          <div class="metric-label">Fake Prob.</div>
        </div>
      </div>
      
      <div class="gauge">
        <div class="gauge-title">📊 ${data.credibility_level}</div>
        <div class="gauge-bar">
          <div class="gauge-fill" style="width: ${data.credibility_score}%; background: ${gaugeColor}"></div>
        </div>
      </div>
  `;
  
  // Key words
  if (data.suspicious_words && data.suspicious_words.length > 0) {
    html += `
      <div class="words">
        <div class="words-title">🔑 Key Indicators</div>
        <div class="word-tags">
          ${data.suspicious_words.slice(0, 8).map(w => 
            `<span class="word-tag ${w.direction}">${w.direction === 'fake' ? '🔴' : '🟢'} ${w.word}</span>`
          ).join('')}
        </div>
      </div>
    `;
  }
  
  html += '</div>';
  resultContainer.innerHTML = html;
}
