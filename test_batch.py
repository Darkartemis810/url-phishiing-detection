#!/usr/bin/env python3
"""
Batch testing script for URL Phishing Detection
Tests multiple URLs and displays results in a table format
"""

import sys
sys.path.append('.')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
from predict_url import extract_features, load_model
import warnings
warnings.filterwarnings('ignore')

def predict_urls_batch(urls, model_path='url_phishing_model.pkl'):
    """Predict multiple URLs"""
    try:
        model, feature_names = load_model(model_path)
    except FileNotFoundError:
        print("❌ Model file not found. Please run the notebook first.")
        return
    
    print("\n" + "="*100)
    print("🔍 BATCH URL PHISHING DETECTION TEST")
    print("="*100)
    
    results = []
    
    for url in urls:
        features = extract_features(url)
        if features is None:
            continue
        
        # Convert to DataFrame with correct feature order
        features_df = pd.DataFrame([features])[feature_names]
        
        prediction = model.predict(features_df)[0]
        probabilities = model.predict_proba(features_df)[0]
        
        results.append({
            'url': url,
            'prediction': 'PHISHING' if prediction == 1 else 'LEGITIMATE',
            'confidence': max(probabilities) * 100,
            'prob_phishing': probabilities[1] * 100
        })
    
    # Display results in table format
    print(f"\n{'#':<4} {'URL':<55} {'PREDICTION':<15} {'CONFIDENCE':<12}")
    print("-"*100)
    
    for i, result in enumerate(results, 1):
        url_display = result['url'][:52] + '...' if len(result['url']) > 55 else result['url']
        
        if result['prediction'] == 'PHISHING':
            status = f"🚨 {result['prediction']}"
        else:
            status = f"✅ {result['prediction']}"
        
        print(f"{i:<4} {url_display:<55} {status:<15} {result['confidence']:>6.2f}%")
    
    print("-"*100)
    
    # Summary statistics
    total = len(results)
    phishing_count = sum(1 for r in results if r['prediction'] == 'PHISHING')
    legitimate_count = total - phishing_count
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total URLs tested: {total}")
    print(f"   Phishing detected: {phishing_count} ({phishing_count/total*100:.1f}%)")
    print(f"   Legitimate URLs:   {legitimate_count} ({legitimate_count/total*100:.1f}%)")
    print("="*100 + "\n")

if __name__ == "__main__":
    # Test URLs - mix of legitimate and phishing
    test_urls = [
        # Legitimate URLs
        "https://www.google.com",
        "https://github.com/microsoft/vscode",
        "https://www.amazon.com/products",
        "https://stackoverflow.com/questions",
        "https://www.wikipedia.org/wiki/Python",
        
        # Suspicious/Phishing URLs
        "http://secure-paypal-login.tk/verify/account.php?id=12345",
        "http://192.168.1.1/banking/login",
        "http://login-facebook-verify.ml/account/confirm",
        "http://amaz0n-security-update.xyz/signin.php?user=12345",
        "http://g00gle-verify-account.com/login?redirect=true",
        "http://secure.apple.id.verify.account-update.tk/signin",
        "http://microsoft-support-team.ga/windows/update.exe",
    ]
    
    predict_urls_batch(test_urls)
