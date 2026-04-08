"""
geo_analytics.py
=================
Geographical analytics for fake news distribution.

Extracts country mentions from text using NLP,
provides data for world heatmap visualization.
"""

import re
from typing import Dict, List, Optional
from collections import Counter

# Country name to ISO code mapping
COUNTRY_DATA = {
    "united states": {"code": "USA", "lat": 39.8, "lon": -98.5},
    "america": {"code": "USA", "lat": 39.8, "lon": -98.5},
    "us": {"code": "USA", "lat": 39.8, "lon": -98.5},
    "united kingdom": {"code": "GBR", "lat": 55.3, "lon": -3.4},
    "uk": {"code": "GBR", "lat": 55.3, "lon": -3.4},
    "britain": {"code": "GBR", "lat": 55.3, "lon": -3.4},
    "india": {"code": "IND", "lat": 20.5, "lon": 78.9},
    "china": {"code": "CHN", "lat": 35.8, "lon": 104.2},
    "russia": {"code": "RUS", "lat": 61.5, "lon": 105.3},
    "brazil": {"code": "BRA", "lat": -14.2, "lon": -51.9},
    "germany": {"code": "DEU", "lat": 51.1, "lon": 10.4},
    "france": {"code": "FRA", "lat": 46.2, "lon": 2.2},
    "japan": {"code": "JPN", "lat": 36.2, "lon": 138.2},
    "australia": {"code": "AUS", "lat": -25.2, "lon": 133.7},
    "canada": {"code": "CAN", "lat": 56.1, "lon": -106.3},
    "south korea": {"code": "KOR", "lat": 35.9, "lon": 127.7},
    "mexico": {"code": "MEX", "lat": 23.6, "lon": -102.5},
    "italy": {"code": "ITA", "lat": 41.8, "lon": 12.5},
    "spain": {"code": "ESP", "lat": 40.4, "lon": -3.7},
    "nigeria": {"code": "NGA", "lat": 9.1, "lon": 8.6},
    "south africa": {"code": "ZAF", "lat": -30.5, "lon": 22.9},
    "pakistan": {"code": "PAK", "lat": 30.3, "lon": 69.3},
    "iran": {"code": "IRN", "lat": 32.4, "lon": 53.6},
    "turkey": {"code": "TUR", "lat": 38.9, "lon": 35.2},
    "egypt": {"code": "EGY", "lat": 26.8, "lon": 30.8},
    "ukraine": {"code": "UKR", "lat": 48.3, "lon": 31.1},
    "poland": {"code": "POL", "lat": 51.9, "lon": 19.1},
    "indonesia": {"code": "IDN", "lat": -0.7, "lon": 113.9},
    "philippines": {"code": "PHL", "lat": 12.8, "lon": 121.7},
    "thailand": {"code": "THA", "lat": 15.8, "lon": 100.9},
}


def extract_countries(text: str) -> List[Dict]:
    """
    Extract country mentions from text.
    
    Args:
        text: News article text
    
    Returns:
        List of dicts with country info and mention count
    """
    text_lower = text.lower()
    found = Counter()
    
    for name, data in COUNTRY_DATA.items():
        # Use word boundary matching
        pattern = r'\b' + re.escape(name) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            code = data["code"]
            found[code] += len(matches)
    
    results = []
    for code, count in found.most_common():
        # Find the country data by code
        for name, data in COUNTRY_DATA.items():
            if data["code"] == code:
                results.append({
                    "country": name.title(),
                    "code": code,
                    "count": count,
                    "lat": data["lat"],
                    "lon": data["lon"],
                })
                break
    
    return results


def generate_heatmap_data(analyses: List[Dict]) -> Dict:
    """
    Generate heatmap data from a collection of analyses.
    
    Args:
        analyses: List of analysis results with text and predictions
    
    Returns:
        Dict with country codes, counts, and coordinates for Plotly
    """
    country_stats = Counter()
    fake_by_country = Counter()
    
    for analysis in analyses:
        text = analysis.get("text", "")
        prediction = analysis.get("prediction", "REAL")
        
        countries = extract_countries(text)
        for country in countries:
            code = country["code"]
            country_stats[code] += country["count"]
            if prediction == "FAKE":
                fake_by_country[code] += country["count"]
    
    # Build Plotly-compatible data
    codes = []
    counts = []
    fake_counts = []
    labels = []
    
    for code, count in country_stats.most_common():
        codes.append(code)
        counts.append(count)
        fake_counts.append(fake_by_country.get(code, 0))
        # Find country name
        for name, data in COUNTRY_DATA.items():
            if data["code"] == code:
                labels.append(name.title())
                break
    
    return {
        "codes": codes,
        "counts": counts,
        "fake_counts": fake_counts,
        "labels": labels,
        "total_countries": len(codes),
    }


# ─── Sample heatmap data for demo ────────────────────────────────────────────
SAMPLE_HEATMAP_DATA = {
    "codes": ["USA", "GBR", "IND", "BRA", "RUS", "CHN", "DEU", "FRA", "NGA", "AUS"],
    "counts": [45, 22, 18, 15, 12, 10, 8, 7, 6, 5],
    "fake_counts": [18, 8, 7, 9, 8, 6, 2, 2, 4, 1],
    "labels": ["United States", "United Kingdom", "India", "Brazil", "Russia",
               "China", "Germany", "France", "Nigeria", "Australia"],
    "total_countries": 10,
}
