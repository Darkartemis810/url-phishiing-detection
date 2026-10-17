#!/usr/bin/env python
"""
Quick Test - Verify model works with real URLs
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from predict_url import predict_url

print("\n" + "="*70)
print("QUICK SYSTEM TEST - URL Phishing Detector")
print("="*70)

# Test URLs
test_cases = [
    ("https://www.google.com", "LEGITIMATE", "Google Search"),
    ("http://paypal-verify.tk", "PHISHING", "Fake PayPal"),
    ("https://github.com", "LEGITIMATE", "GitHub"),
    ("http://g00gle.com", "PHISHING", "Typosquatting"),
]

print("\nTesting model with 4 URLs...\n")

passed = 0
for url, expected, description in test_cases:
    prediction, probability = predict_url(url)
    result = "PHISHING" if prediction == 1 else "LEGITIMATE"
    confidence = probability[prediction] * 100
    
    status = "✅ PASS" if result == expected else "❌ FAIL"
    passed += (result == expected)
    
    print(f"{status} | {description:<20} | {result:<12} | {confidence:.1f}%")

print("\n" + "="*70)
print(f"Results: {passed}/4 tests passed")
print("="*70)

if passed == 4:
    print("\n✅ System ready for demo!")
else:
    print("\n⚠️ Some tests failed - check model file")

print()
