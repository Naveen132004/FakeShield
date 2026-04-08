"""Quick test - writes results to JSON file."""
import json
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from predict import FakeNewsPredictor

predictor = FakeNewsPredictor()

tests = [
    {"text": "BREAKING: Scientists discover that 5G towers cause mind control! The government is hiding the truth from everyone! Share before they delete this!", "expected": "FAKE"},
    {"text": "According to Reuters, the Federal Reserve announced today that interest rates will remain unchanged at 5.25 percent, citing stable inflation data collected through nationwide surveys.", "expected": "REAL"},
    {"text": "EXPOSED: The Illuminati has been controlling the media for years! Secret document leaked reveals the truth they want to hide!", "expected": "FAKE"},
    {"text": "A study published in Nature found that regular exercise reduces cardiovascular risk by 30 percent. The research was peer-reviewed and conducted over 5 years at multiple institutions.", "expected": "REAL"},
]

results = []
for i, test in enumerate(tests):
    r = predictor.predict(test["text"])
    results.append({
        "test": i + 1,
        "expected": test["expected"],
        "prediction": r["prediction"],
        "confidence": r["confidence"],
        "credibility_score": r["credibility_score"],
        "credibility_level": r["credibility_level"],
        "correct": r["prediction"] == test["expected"],
        "top_words": [w["word"] for w in r.get("suspicious_words", [])[:5]]
    })

output = {
    "total_tests": len(tests),
    "correct": sum(r["correct"] for r in results),
    "results": results
}

with open("test_results.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Done! {output['correct']}/{output['total_tests']} correct. See test_results.json")
