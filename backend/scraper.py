"""
scraper.py
==========
Web scraping service for extracting article content from URLs.
Uses BeautifulSoup for HTML parsing.
"""

import re
import requests
from typing import Dict, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# Common user agent to avoid blocks
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Tags that typically contain article content
ARTICLE_TAGS = ['article', 'main', 'section']
CONTENT_CLASSES = ['article-body', 'article-content', 'post-content', 
                   'entry-content', 'story-body', 'content-body']


def extract_article(url: str, timeout: int = 15) -> Dict:
    """
    Extract article content from a URL.
    
    Args:
        url: URL of the news article
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with title, text, domain, etc.
    """
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    
    # Fetch page
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=timeout, 
                                allow_redirects=True)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ConnectionError(f"Request timed out for: {url}")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to: {url}")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"HTTP error for {url}: {e}")
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract title
    title = _extract_title(soup)
    
    # Extract main text content
    text = _extract_text(soup)
    
    # Extract metadata
    domain = parsed.netloc.replace('www.', '')
    
    return {
        "title": title,
        "text": text,
        "domain": domain,
        "url": url,
        "text_length": len(text),
        "status_code": response.status_code,
    }


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract article title from HTML."""
    # Try og:title first
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    
    # Try h1
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    
    # Try title tag
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)
    
    return "Unknown Title"


def _extract_text(soup: BeautifulSoup) -> str:
    """
    Extract main article text from HTML.
    
    Uses multiple strategies to find the article body.
    """
    # Remove script, style, nav, footer, header elements
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header',
                               'aside', 'form', 'noscript', 'iframe']):
        tag.decompose()
    
    # Strategy 1: Look for article-specific tags
    article = soup.find('article')
    if article:
        text = _clean_text(article.get_text(separator=' ', strip=True))
        if len(text) > 100:
            return text
    
    # Strategy 2: Look for common content class names
    for class_name in CONTENT_CLASSES:
        content = soup.find(class_=re.compile(class_name, re.I))
        if content:
            text = _clean_text(content.get_text(separator=' ', strip=True))
            if len(text) > 100:
                return text
    
    # Strategy 3: Look for main or content divs
    for tag_name in ['main', 'section']:
        tag = soup.find(tag_name)
        if tag:
            text = _clean_text(tag.get_text(separator=' ', strip=True))
            if len(text) > 100:
                return text
    
    # Strategy 4: Look for the div with the most paragraphs
    best_div = None
    max_paragraphs = 0
    
    for div in soup.find_all('div'):
        paragraphs = div.find_all('p')
        if len(paragraphs) > max_paragraphs:
            max_paragraphs = len(paragraphs)
            best_div = div
    
    if best_div and max_paragraphs >= 3:
        text = ' '.join(p.get_text(strip=True) for p in best_div.find_all('p'))
        text = _clean_text(text)
        if len(text) > 100:
            return text
    
    # Strategy 5: Fall back to all paragraphs
    paragraphs = soup.find_all('p')
    if paragraphs:
        text = ' '.join(p.get_text(strip=True) for p in paragraphs)
        text = _clean_text(text)
        if len(text) > 50:
            return text
    
    # Last resort: body text
    body = soup.find('body')
    if body:
        return _clean_text(body.get_text(separator=' ', strip=True))[:5000]
    
    return ""


def _clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove very short lines (likely navigation elements)
    lines = text.split('. ')
    lines = [l for l in lines if len(l) > 20]
    return '. '.join(lines)
