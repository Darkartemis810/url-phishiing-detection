import time
import math
from collections import Counter
import re
from urllib.parse import urlparse
import numpy as np
import pandas as pd
import tldextract
import pickle
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("="*75)
print("🛡️ TRAINING ADVANCED URL PHISHING DETECTION MODEL (27 FEATURES)")
print("="*75)

# Legitimate URLs patterns
legit_urls = [
    'https://www.google.com',
    'https://github.com/user/repo',
    'https://www.amazon.com/products',
    'https://stackoverflow.com/questions',
    'https://www.microsoft.com',
    'https://www.apple.com/iphone',
    'https://www.netflix.com',
    'https://www.facebook.com',
    'https://www.twitter.com',
    'https://www.linkedin.com/in/user',
]

# Phishing URLs patterns (including deceptive, typosquatted, and free TLD patterns)
phishing_urls = [
    'http://secure-paypal-verify.com/login.php?id=123456',
    'http://192.168.1.1/banking/login',
    'https://www.goog1e.com/verify-account',
    'http://amaz0n-security.net/update-payment',
    'http://login-facebook-secure.tk/verify',
    'http://www.paypa1-secure.com/webscr.php',
    'http://microsoft-support.xyz/update',
    'http://appIe-icloud.com/verify-id',
    'http://account-netflix.ml/billing',
    'http://secure.login.update.verification.com.suspicious-domain.tk',
    'http://g00gle.com',
    'http://paypa1.com',
    'http://amaz0n.com',
    'http://faceb00k.com',
    'http://appIe.com'
]

np.random.seed(42)

def generate_variations(urls, count):
    result = []
    for _ in range(count):
        base = np.random.choice(urls)
        if np.random.rand() > 0.35:
            result.append(base + '/' + ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyz0123456789-_'), 
                                                                np.random.randint(5, 20))))
        else:
            result.append(base)
    return result

legit_samples = legit_urls + generate_variations(legit_urls, 490)
phishing_samples = phishing_urls + generate_variations(phishing_urls, 485)

urls = legit_samples + phishing_samples
labels = [0] * len(legit_samples) + [1] * len(phishing_samples)

df_urls = pd.DataFrame({'url': urls, 'label': labels})
df_urls = df_urls.sample(frac=1, random_state=42).reset_index(drop=True)

# Save raw dataset
urls_csv = r"d:\Url phishing\phishing_urls_dataset.csv"
df_urls.to_csv(urls_csv, index=False)
print(f"✅ Generated {len(df_urls)} URLs dataset -> {urls_csv}")

# Constants for Feature Extraction
IP_PATTERN = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
SUSPICIOUS_TLDS = {'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top'}
SUSPICIOUS_WORDS = ['verify', 'account', 'secure', 'update', 'login', 'banking', 'confirm']
SHORTENERS = {'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'bitly.com'}
TARGET_BRANDS = [
    'google', 'paypal', 'microsoft', 'apple', 'amazon',
    'netflix', 'facebook', 'instagram', 'twitter', 'linkedin',
    'github', 'whatsapp', 'chase', 'wellsfargo', 'bankofamerica'
]

def levenshtein(s1, s2):
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
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())

def extract_features(url):
    features = {}
    parsed = urlparse(url)
    ext = tldextract.extract(url)
    
    # 1. URL Length
    features['url_length'] = len(url)
    # 2. Domain Length
    features['domain_length'] = len(parsed.netloc)
    # 3. Protocol (HTTPS)
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
    # 18. Domain Shannon Entropy (measures randomness/DGA)
    features['domain_entropy'] = calc_entropy(parsed.netloc)
    # 19. Punycode / Homograph attack detection
    features['has_punycode'] = 1 if 'xn--' in url.lower() or any(ord(c) > 127 for c in url) else 0
    # 20. Brand Typosquatting / Levenshtein Distance
    features['has_brand_spoof'] = check_brand_spoof(parsed.netloc)
    
    return features

print("Extracting 27 features for all URLs...", flush=True)
feat_list = [extract_features(u) for u in df_urls['url']]
df_features = pd.DataFrame(feat_list)
feature_names = list(df_features.columns)

df_features_with_label = df_features.copy()
df_features_with_label['label'] = df_urls['label']
features_csv = r"d:\Url phishing\phishing_features_dataset.csv"
df_features_with_label.to_csv(features_csv, index=False)
print(f"✅ Saved features dataset -> {features_csv} ({len(feature_names)} features)")

# Train-Test Split (80/20 Stratified)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

X = df_features
y = df_urls['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {X_train.shape[0]} samples | Test set: {X_test.shape[0]} samples")

# Benchmark 4 ML Models
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

models = {
    'Logistic Regression': (LogisticRegression(max_iter=1000, random_state=42), True),
    'Decision Tree': (DecisionTreeClassifier(max_depth=15, random_state=42), False),
    'Gradient Boosting': (GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42), False),
    'Random Forest (Ours)': (RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1, verbose=0), False),
}

benchmark_rows = []
for name, (clf, use_scale) in models.items():
    t0 = time.time()
    xtr = X_train_scaled if use_scale else X_train
    xte = X_test_scaled if use_scale else X_test
    
    clf.fit(xtr, y_train)
    train_time = time.time() - t0
    
    y_pred = clf.predict(xte)
    y_prob = clf.predict_proba(xte)[:, 1] if hasattr(clf, "predict_proba") else y_pred
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob)
    cv = cross_val_score(clf, xtr, y_train, cv=5, scoring='accuracy').mean()
    
    benchmark_rows.append({
        'Model': name,
        'Accuracy': f"{acc*100:.2f}%",
        'Precision': f"{prec*100:.2f}%",
        'Recall': f"{rec*100:.2f}%",
        'F1-Score': f"{f1:.4f}",
        'ROC-AUC': f"{roc:.4f}",
        '5-Fold CV': f"{cv*100:.2f}%",
        'Train Time': f"{train_time*1000:.1f} ms"
    })

bench_df = pd.DataFrame(benchmark_rows)
bench_csv = r"d:\Url phishing\model_benchmark_results.csv"
bench_df.to_csv(bench_csv, index=False)

print("\n" + "="*80)
print("📊 MULTI-MODEL BENCHMARK COMPARISON TABLE")
print("="*80)
print(bench_df.to_string(index=False))
print("="*80)

# Save Primary Random Forest Model
rf_model = models['Random Forest (Ours)'][0]
model_path = r"d:\Url phishing\url_phishing_model.pkl"

with open(model_path, 'wb') as f:
    pickle.dump({
        'model': rf_model,
        'feature_names': feature_names
    }, f)

print(f"\n✅ Serialized Random Forest model saved to: {model_path} ({os.path.getsize(model_path)/1024:.1f} KB)")

# Test quick sample URLs
quick_cases = [
    ("https://www.google.com", 0, "Google Search"),
    ("http://paypal-verify.tk", 1, "Fake PayPal (.tk)"),
    ("https://github.com", 0, "GitHub Platform"),
    ("http://g00gle.com", 1, "Brand Typosquatting")
]

print("\n" + "="*70)
print("🧪 VALIDATING PREDICTIONS (ALL 4 SAMPLE CASES):")
print("="*70)
all_pass = True
for url, expected, desc in quick_cases:
    fvec = pd.DataFrame([extract_features(url)])[feature_names]
    pred = rf_model.predict(fvec)[0]
    prob = rf_model.predict_proba(fvec)[0]
    res_label = "PHISHING" if pred == 1 else "LEGITIMATE"
    passed = (pred == expected)
    all_pass = all_pass and passed
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {desc:<22} | {res_label:<12} | Conf: {prob[pred]*100:.2f}%")

print("="*70)
if all_pass:
    print("🎉 ALL 4/4 SYSTEM TESTS PASSED SUCCESSFULLY (100% PASS RATE)!")
else:
    print("⚠️ Warning: Some sample tests did not match expected.")

print("\nTraining and benchmarking completed successfully!")
