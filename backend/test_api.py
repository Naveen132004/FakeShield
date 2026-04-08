"""Test the backend API endpoints."""
import requests
import json

BASE = "http://localhost:8000"

def test_health():
    print("=== Health Check ===")
    r = requests.get(f"{BASE}/api/health")
    print(f"  Status: {r.status_code}")
    print(f"  Response: {json.dumps(r.json(), indent=2)}")
    return r.status_code == 200

def test_predict_fake():
    print("\n=== Predict FAKE news ===")
    r = requests.post(f"{BASE}/api/predict", json={
        "text": "BREAKING: Scientists discover that 5G towers cause mind control! The government is hiding the truth from everyone! Share before they delete this!"
    })
    data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Prediction: {data.get('prediction')}")
    print(f"  Confidence: {data.get('confidence')}%")
    print(f"  Credibility: {data.get('credibility_score')}/100 ({data.get('credibility_level')})")
    return data.get("prediction") == "FAKE"

def test_predict_real():
    print("\n=== Predict REAL news ===")
    r = requests.post(f"{BASE}/api/predict", json={
        "text": "According to Reuters, the Federal Reserve announced today that interest rates will remain unchanged at 5.25 percent, citing stable inflation data collected through nationwide surveys."
    })
    data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Prediction: {data.get('prediction')}")
    print(f"  Confidence: {data.get('confidence')}%")
    print(f"  Credibility: {data.get('credibility_score')}/100 ({data.get('credibility_level')})")
    return data.get("prediction") == "REAL"

def test_monitor():
    print("\n=== Monitor News ===")
    r = requests.get(f"{BASE}/api/monitor")
    data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Articles: {data.get('analyzed_count')}")
    print(f"  Fake: {data.get('fake_count')}, Real: {data.get('real_count')}")
    for art in data.get("articles", [])[:3]:
        print(f"    - [{art['prediction']}] {art['title'][:60]}...")
    return r.status_code == 200

def test_dashboard():
    print("\n=== Dashboard Stats ===")
    r = requests.get(f"{BASE}/api/dashboard")
    data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Total analyzed: {data.get('total_analyzed')}")
    print(f"  Fake: {data.get('fake_count')}, Real: {data.get('real_count')}")
    print(f"  Avg credibility: {data.get('average_credibility')}")
    return r.status_code == 200

def test_history():
    print("\n=== History ===")
    r = requests.get(f"{BASE}/api/history")
    data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  Total records: {data.get('total')}")
    for item in data.get("items", [])[:3]:
        print(f"    - [{item['prediction']}] {item['text_preview'][:50]}...")
    return r.status_code == 200

if __name__ == "__main__":
    results = []
    results.append(("Health",    test_health()))
    results.append(("Fake",      test_predict_fake()))
    results.append(("Real",      test_predict_real()))
    results.append(("Monitor",   test_monitor()))
    results.append(("Dashboard", test_dashboard()))
    results.append(("History",   test_history()))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name:12s} -> {status}")
    
    passed = sum(1 for _, p in results if p)
    print(f"\n  {passed}/{len(results)} tests passed")
