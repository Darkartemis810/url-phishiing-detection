#!/usr/bin/env python
"""
CLI Tool for URL Phishing Detection
Uses the trained Random Forest model to predict if a URL is phishing or legitimate.
"""

import pickle
import sys
import re
from urllib.parse import urlparse
import tldextract
import pandas as pd
import warnings
import os

# Suppress all warnings for clean demo output
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Precompiled constants for efficient feature extraction
IP_PATTERN = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
SUSPICIOUS_TLDS = {'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top'}
SUSPICIOUS_WORDS = ['verify', 'account', 'secure', 'update', 'login', 'banking', 'confirm']
SHORTENERS = {'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'bitly.com'}
TARGET_BRANDS = [
    'google', 'paypal', 'microsoft', 'apple', 'amazon',
    'netflix', 'facebook', 'instagram', 'twitter', 'linkedin',
    'github', 'whatsapp', 'chase', 'wellsfargo', 'bankofamerica'
]

import math
from collections import Counter


def levenshtein(s1, s2):
    """Compute Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            ins = prev[j + 1] + 1
            dels = curr[j] + 1
            subs = prev[j] + (c1 != c2)
            curr.append(min(ins, dels, subs))
        prev = curr
    return prev[-1]


def check_brand_spoof(domain):
    """Check if domain is typosquatting a known brand"""
    tokens = re.split(r'[-._]', domain.lower())
    for token in tokens:
        if len(token) < 4:
            continue
        for brand in TARGET_BRANDS:
            dist = levenshtein(token, brand)
            if 1 <= dist <= 2:
                return 1
    return 0


def calc_entropy(text):
    """Calculate Shannon entropy of a string (measures randomness/DGA)"""
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())

# Model cache to avoid reloading model from disk on every prediction
_CACHED_MODEL = None
_CACHED_FEATURE_NAMES = None
_CACHED_MODEL_PATH = None


def load_model(model_path='url_phishing_model.pkl'):
    """Load and cache model in memory for high-efficiency prediction"""
    global _CACHED_MODEL, _CACHED_FEATURE_NAMES, _CACHED_MODEL_PATH
    if _CACHED_MODEL is None or _CACHED_MODEL_PATH != model_path:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file '{model_path}' not found.")
        with open(model_path, 'rb') as file:
            data = pickle.load(file)
            _CACHED_MODEL = data['model']
            _CACHED_FEATURE_NAMES = data['feature_names']
            _CACHED_MODEL_PATH = model_path
            _CACHED_MODEL.verbose = 0
    return _CACHED_MODEL, _CACHED_FEATURE_NAMES


def extract_features(url):
    """Extract 27 lexical, structural, and cybersecurity features from a URL"""
    features = {}
    
    # Parse URL
    parsed = urlparse(url)
    ext = tldextract.extract(url)
    
    # 1. URL Length
    features['url_length'] = len(url)
    
    # 2. Domain Length
    features['domain_length'] = len(parsed.netloc)
    
    # 3. Protocol
    features['is_https'] = 1 if parsed.scheme == 'https' else 0
    
    # 4. Special character counts
    features['num_dots'] = url.count('.')
    features['num_hyphens'] = url.count('-')
    features['num_underscores'] = url.count('_')
    features['num_slashes'] = url.count('/')
    features['num_question'] = url.count('?')
    features['num_equal'] = url.count('=')
    features['num_at'] = url.count('@')
    features['num_ampersand'] = url.count('&')
    
    # 5. Digit count
    features['num_digits'] = sum(c.isdigit() for c in url)
    
    # 6. IP address presence
    features['has_ip'] = 1 if IP_PATTERN.search(url) else 0
    
    # 7. Port presence
    features['has_port'] = 1 if parsed.port else 0
    
    # 8. Subdomain count
    features['num_subdomains'] = len(ext.subdomain.split('.')) if ext.subdomain else 0
    
    # 9. Path length
    features['path_length'] = len(parsed.path)
    
    # 10. Query length
    features['query_length'] = len(parsed.query)
    
    # 11. Fragment length
    features['fragment_length'] = len(parsed.fragment)
    
    # 12. Suspicious TLDs
    features['has_suspicious_tld'] = 1 if ext.suffix in SUSPICIOUS_TLDS else 0
    
    # 13. Double slash in path
    features['double_slash_in_path'] = 1 if '//' in parsed.path else 0
    
    # 14. Suspicious words
    features['has_suspicious_word'] = 1 if any(word in url.lower() for word in SUSPICIOUS_WORDS) else 0
    
    # 15. Length of longest word in domain
    domain_words = re.split(r'[.-]', parsed.netloc)
    features['max_domain_word_length'] = max([len(w) for w in domain_words]) if domain_words else 0
    
    # 16. Ratio of digits to characters
    features['digit_ratio'] = features['num_digits'] / len(url) if len(url) > 0 else 0
    
    # === ADVANCED CYBERSECURITY FEATURES ===
    # 17. URL Shortener detection
    domain_only = parsed.netloc.lower().split(':')[0]
    features['is_shortened'] = 1 if domain_only in SHORTENERS else 0
    
    # 18. Domain Shannon Entropy
    features['domain_entropy'] = calc_entropy(parsed.netloc)
    
    # 19. Punycode / Homograph attack detection
    features['has_punycode'] = 1 if 'xn--' in url.lower() or any(ord(c) > 127 for c in url) else 0
    
    # 20. Brand Typosquatting / Levenshtein Distance
    features['has_brand_spoof'] = check_brand_spoof(parsed.netloc)
    
    return features


def predict_url(url, model_path='url_phishing_model.pkl'):
    """Predict if a URL is phishing or legitimate"""
    try:
        # Load model with caching
        model, feature_names = load_model(model_path)
        
        # Extract features
        features = extract_features(url)
        
        # Convert to DataFrame with correct feature order
        features_df = pd.DataFrame([features])[feature_names]
        
        # Predict
        prediction = model.predict(features_df)[0]
        probability = model.predict_proba(features_df)[0]
        
        return prediction, probability
        
    except FileNotFoundError:
        print(f"Error: Model file '{model_path}' not found.")
        print("Please run the Jupyter notebook first to train and save the model.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main CLI function"""
    print("=" * 70)
    print("URL Phishing Detection - Random Forest Classifier")
    print("=" * 70)
    
    # Get URL from command line or user input
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter URL to analyze: ").strip()
    
    if not url:
        print("Error: No URL provided.")
        sys.exit(1)
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        print(f"Warning: No protocol specified. Assuming 'http://'")
        url = 'http://' + url
    
    print(f"\nAnalyzing URL: {url}")
    print("-" * 70)
    
    # Predict
    prediction, probability = predict_url(url)
    
    # Display results
    label = "PHISHING ⚠️" if prediction == 1 else "LEGITIMATE ✓"
    confidence = probability[prediction] * 100
    
    print(f"\nPrediction: {label}")
    print(f"Confidence: {confidence:.2f}%")
    print(f"\nDetailed Probabilities:")
    print(f"  Legitimate: {probability[0]:.4f} ({probability[0]*100:.2f}%)")
    print(f"  Phishing:   {probability[1]:.4f} ({probability[1]*100:.2f}%)")
    print("=" * 70)
    
    if prediction == 1:
        print("\n⚠️  WARNING: This URL appears to be a PHISHING attempt!")
        print("   Do NOT enter sensitive information on this site.")
    else:
        print("\n✓ This URL appears to be legitimate.")
        print("  However, always exercise caution when entering sensitive data.")
    
    print()


if __name__ == "__main__":
    main()
