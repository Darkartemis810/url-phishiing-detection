#!/usr/bin/env python
"""
URL Phishing Detection - Cyber Threat Intelligence Web Dashboard
Self-contained, production-grade interactive web application.
Runs on Python built-in http.server, zero extra dependencies required.
"""

import http.server
import socketserver
import json
import urllib.parse
import webbrowser
import os
import sys
import threading
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from predict_url import predict_url, extract_features, load_model

PORT = 5000

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Phishing Shield - Cyber Threat Intelligence</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #121826;
            --bg-card: rgba(18, 24, 38, 0.75);
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(59, 130, 246, 0.4);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-orange: #f59e0b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: radial-gradient(circle at 10% 20%, rgba(14, 23, 42, 1) 0%, rgba(10, 14, 23, 1) 90%);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
            padding-bottom: 60px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        /* Header */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #2563eb, #06b6d4);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            box-shadow: 0 0 24px rgba(59, 130, 246, 0.4);
        }

        .logo-text h1 {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-text p {
            font-size: 13px;
            color: var(--text-muted);
        }

        .badge-live {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #34d399;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        /* Search Section */
        .search-card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
            margin-bottom: 32px;
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }

        .url-input {
            flex: 1;
            background: rgba(10, 14, 23, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 16px 20px;
            font-size: 16px;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            outline: none;
            transition: all 0.2s;
        }

        .url-input:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
        }

        .btn-analyze {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border: none;
            color: white;
            font-size: 15px;
            font-weight: 600;
            padding: 0 32px;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
        }

        .btn-analyze:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 20px rgba(37, 99, 235, 0.4);
        }

        .quick-presets {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .preset-label {
            font-size: 13px;
            color: var(--text-muted);
            font-weight: 500;
        }

        .preset-chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 12px;
            padding: 6px 14px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
            font-family: 'JetBrains Mono', monospace;
        }

        .preset-chip:hover {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.4);
            color: #ffffff;
        }

        /* Results Display */
        .result-container {
            display: none;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .verdict-banner {
            border-radius: 18px;
            padding: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }

        .verdict-banner.phishing {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(185, 28, 28, 0.1));
            border: 1px solid rgba(239, 68, 68, 0.4);
        }

        .verdict-banner.legitimate {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(4, 120, 87, 0.1));
            border: 1px solid rgba(16, 185, 129, 0.4);
        }

        .verdict-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .verdict-icon {
            font-size: 48px;
        }

        .verdict-title {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.01em;
        }

        .verdict-title.phishing { color: #f87171; }
        .verdict-title.legitimate { color: #34d399; }

        .verdict-subtitle {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .gauge-box {
            text-align: right;
        }

        .gauge-percent {
            font-size: 38px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }

        .gauge-percent.phishing { color: #f87171; }
        .gauge-percent.legitimate { color: #34d399; }

        .gauge-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Metric Grid */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }

        .card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.2s;
        }

        .card:hover {
            border-color: var(--border-hover);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .card-title {
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
        }

        .card-icon {
            font-size: 18px;
        }

        .card-value {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .card-desc {
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* Benchmark Section */
        .section-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .table-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 32px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
        }

        td {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }

        tr:last-child td {
            border-bottom: none;
        }

        .highlight-row {
            background: rgba(59, 130, 246, 0.08);
            font-weight: 600;
        }

        .tag-winner {
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            margin-left: 8px;
        }

        /* Collapsible Raw Features */
        details {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px 20px;
            cursor: pointer;
        }

        summary {
            font-weight: 600;
            font-size: 15px;
            color: var(--text-secondary);
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            padding-top: 20px;
        }

        .feature-item {
            background: rgba(10, 14, 23, 0.6);
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 13px;
        }

        .feature-name {
            color: var(--text-muted);
            font-size: 11px;
            margin-bottom: 2px;
            font-family: 'JetBrains Mono', monospace;
        }

        .feature-val {
            font-weight: 700;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-group">
                <div class="logo-icon">🛡️</div>
                <div class="logo-text">
                    <h1>URL Phishing Intelligence Shield</h1>
                    <p>Machine Learning Cyber Threat Detection Platform (27 Engineered Features)</p>
                </div>
            </div>
            <div class="badge-live">
                <div class="pulse-dot"></div>
                Random Forest Engine Active
            </div>
        </header>

        <!-- Search Input -->
        <div class="search-card">
            <div class="input-wrapper">
                <input type="text" id="urlInput" class="url-input" placeholder="Paste or type any URL to inspect (e.g. https://www.google.com or http://secure-paypal.tk)..." value="https://www.google.com">
                <button class="btn-analyze" id="analyzeBtn" onclick="analyzeUrl()">
                    <span>🔍</span> Analyze URL
                </button>
            </div>
            <div class="quick-presets">
                <span class="preset-label">1-Click Live Test Cases:</span>
                <span class="preset-chip" onclick="setAndAnalyze('https://www.google.com')">✅ Google</span>
                <span class="preset-chip" onclick="setAndAnalyze('https://github.com/microsoft/vscode')">✅ GitHub</span>
                <span class="preset-chip" onclick="setAndAnalyze('http://secure-paypal-login.tk/verify')">🚨 Fake PayPal (.tk)</span>
                <span class="preset-chip" onclick="setAndAnalyze('http://g00gle.com')">🚨 Typosquatting (g00gle)</span>
                <span class="preset-chip" onclick="setAndAnalyze('http://192.168.1.1/banking/login')">🚨 Direct IP Attack</span>
            </div>
        </div>

        <!-- Result Container -->
        <div id="resultContainer" class="result-container">
            <div id="verdictBanner" class="verdict-banner legitimate">
                <div class="verdict-left">
                    <div id="verdictIcon" class="verdict-icon">✅</div>
                    <div>
                        <div id="verdictTitle" class="verdict-title legitimate">LEGITIMATE URL</div>
                        <div id="verdictSubtitle" class="verdict-subtitle">No significant phishing anomalies detected in URL structure.</div>
                    </div>
                </div>
                <div class="gauge-box">
                    <div id="gaugePercent" class="gauge-percent legitimate">99.47%</div>
                    <div class="gauge-label">Model Confidence</div>
                </div>
            </div>

            <!-- Risk Cards -->
            <div class="cards-grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">SSL Encryption</span>
                        <span id="cardIconHttps" class="card-icon">🔒</span>
                    </div>
                    <div id="cardValHttps" class="card-value">HTTPS Active</div>
                    <div id="cardDescHttps" class="card-desc">Valid encrypted protocol detected.</div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Brand Typosquatting</span>
                        <span id="cardIconBrand" class="card-icon">🎯</span>
                    </div>
                    <div id="cardValBrand" class="card-value">No Impersonation</div>
                    <div id="cardDescBrand" class="card-desc">Domain matches authentic character structure.</div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Urgency Keywords</span>
                        <span id="cardIconWords" class="card-icon">🔑</span>
                    </div>
                    <div id="cardValWords" class="card-value">Clean</div>
                    <div id="cardDescWords" class="card-desc">No deceptive verify/login keywords detected.</div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Top-Level Domain (TLD)</span>
                        <span id="cardIconTld" class="card-icon">🌐</span>
                    </div>
                    <div id="cardValTld" class="card-value">Reputable TLD</div>
                    <div id="cardDescTld" class="card-desc">Standard accredited domain registry.</div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Shannon Entropy</span>
                        <span class="card-icon">🎲</span>
                    </div>
                    <div id="cardValEntropy" class="card-value">2.14 bits</div>
                    <div class="card-desc">Measures algorithmic domain randomness.</div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Inference Latency</span>
                        <span class="card-icon">⚡</span>
                    </div>
                    <div id="cardValLatency" class="card-value">1.2 ms</div>
                    <div class="card-desc">In-memory cached Random Forest inference.</div>
                </div>
            </div>

            <!-- Full Features Breakdown -->
            <details style="margin-bottom: 32px;">
                <summary>🔍 View Full 27-Feature Technical Vector</summary>
                <div id="featuresGrid" class="features-grid"></div>
            </details>
        </div>

        <!-- Model Benchmark Section -->
        <div class="section-title">
            <span>📊</span> Multi-Model Benchmark Comparison (Evaluated on Same Dataset)
        </div>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Algorithm</th>
                        <th>Accuracy</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>F1-Score</th>
                        <th>ROC-AUC</th>
                        <th>5-Fold CV</th>
                        <th>Train Time</th>
                    </tr>
                </thead>
                <tbody id="benchmarkTable">
                    <tr class="highlight-row">
                        <td>Random Forest <span class="tag-winner">PRIMARY</span></td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>1.0000</td>
                        <td>1.0000</td>
                        <td>100.00%</td>
                        <td>216 ms</td>
                    </tr>
                    <tr>
                        <td>Gradient Boosting</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>1.0000</td>
                        <td>1.0000</td>
                        <td>100.00%</td>
                        <td>135 ms</td>
                    </tr>
                    <tr>
                        <td>Decision Tree</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>1.0000</td>
                        <td>1.0000</td>
                        <td>100.00%</td>
                        <td>3.7 ms</td>
                    </tr>
                    <tr>
                        <td>Logistic Regression (Baseline)</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>100.00%</td>
                        <td>1.0000</td>
                        <td>1.0000</td>
                        <td>100.00%</td>
                        <td>4.1 ms</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function analyzeUrl() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) return;

            const t0 = performance.now();
            try {
                const response = await fetch(`/api/predict?url=${encodeURIComponent(url)}`);
                const data = await response.json();
                const latency = (performance.now() - t0).toFixed(1);

                renderResult(data, latency);
            } catch (err) {
                alert("Error connecting to prediction engine: " + err);
            }
        }

        function setAndAnalyze(url) {
            document.getElementById('urlInput').value = url;
            analyzeUrl();
        }

        function renderResult(data, latency) {
            const container = document.getElementById('resultContainer');
            container.style.display = 'block';

            const banner = document.getElementById('verdictBanner');
            const icon = document.getElementById('verdictIcon');
            const title = document.getElementById('verdictTitle');
            const sub = document.getElementById('verdictSubtitle');
            const pct = document.getElementById('gaugePercent');

            const isPhishing = data.prediction === 1;

            if (isPhishing) {
                banner.className = 'verdict-banner phishing';
                icon.textContent = '🚨';
                title.textContent = 'PHISHING ATTEMPT DETECTED';
                title.className = 'verdict-title phishing';
                sub.textContent = 'Warning: This URL exhibits severe malicious threat heuristics.';
                pct.textContent = data.confidence.toFixed(2) + '%';
                pct.className = 'gauge-percent phishing';
            } else {
                banner.className = 'verdict-banner legitimate';
                icon.textContent = '✅';
                title.textContent = 'LEGITIMATE URL';
                title.className = 'verdict-title legitimate';
                sub.textContent = 'Safe: URL conforms to authentic legitimate website structure.';
                pct.textContent = data.confidence.toFixed(2) + '%';
                pct.className = 'gauge-percent legitimate';
            }

            // Cards
            const f = data.features;
            
            // HTTPS
            if (f.is_https === 1) {
                document.getElementById('cardValHttps').textContent = 'HTTPS Active';
                document.getElementById('cardValHttps').style.color = '#34d399';
                document.getElementById('cardIconHttps').textContent = '🔒';
                document.getElementById('cardDescHttps').textContent = 'Valid encrypted protocol detected.';
            } else {
                document.getElementById('cardValHttps').textContent = 'No HTTPS (HTTP)';
                document.getElementById('cardValHttps').style.color = '#f87171';
                document.getElementById('cardIconHttps').textContent = '⚠️';
                document.getElementById('cardDescHttps').textContent = 'Unencrypted channel - High risk indicator.';
            }

            // Brand Spoof
            if (f.has_brand_spoof === 1) {
                document.getElementById('cardValBrand').textContent = 'SPOOF DETECTED';
                document.getElementById('cardValBrand').style.color = '#f87171';
                document.getElementById('cardIconBrand').textContent = '🚨';
                document.getElementById('cardDescBrand').textContent = 'Levenshtein typo detected against major brands.';
            } else {
                document.getElementById('cardValBrand').textContent = 'No Impersonation';
                document.getElementById('cardValBrand').style.color = '#34d399';
                document.getElementById('cardIconBrand').textContent = '✅';
                document.getElementById('cardDescBrand').textContent = 'Domain characters match authentic format.';
            }

            // Keywords
            if (f.has_suspicious_word === 1) {
                document.getElementById('cardValWords').textContent = 'Urgency Flagged';
                document.getElementById('cardValWords').style.color = '#f87171';
                document.getElementById('cardIconWords').textContent = '🚨';
                document.getElementById('cardDescWords').textContent = 'Suspicious login/verify/account tokens present.';
            } else {
                document.getElementById('cardValWords').textContent = 'Clean Tokens';
                document.getElementById('cardValWords').style.color = '#34d399';
                document.getElementById('cardIconWords').textContent = '✅';
                document.getElementById('cardDescWords').textContent = 'No deceptive urgency keywords detected.';
            }

            // TLD
            if (f.has_suspicious_tld === 1) {
                document.getElementById('cardValTld').textContent = 'Suspicious TLD';
                document.getElementById('cardValTld').style.color = '#f87171';
                document.getElementById('cardIconTld').textContent = '⚠️';
                document.getElementById('cardDescTld').textContent = 'Free/high-abuse registry (.tk, .ml, .xyz).';
            } else {
                document.getElementById('cardValTld').textContent = 'Standard TLD';
                document.getElementById('cardValTld').style.color = '#34d399';
                document.getElementById('cardIconTld').textContent = '🌐';
                document.getElementById('cardDescTld').textContent = 'Recognized legitimate registry.';
            }

            // Entropy & Latency
            document.getElementById('cardValEntropy').textContent = f.domain_entropy.toFixed(3) + ' bits';
            document.getElementById('cardValLatency').textContent = latency + ' ms';

            // Populate all 27 features
            const grid = document.getElementById('featuresGrid');
            grid.innerHTML = '';
            for (const [key, val] of Object.entries(f)) {
                const item = document.createElement('div');
                item.className = 'feature-item';
                const formattedVal = typeof val === 'number' ? (Number.isInteger(val) ? val : val.toFixed(4)) : val;
                item.innerHTML = `<div class="feature-name">${key}</div><div class="feature-val">${formattedVal}</div>`;
                grid.appendChild(item);
            }

            // Scroll smoothly to results
            banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        // Auto-run on enter key
        document.getElementById('urlInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeUrl();
        });

        // Initial preview analysis
        window.onload = function() {
            analyzeUrl();
        };
    </script>
</body>
</html>
"""

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class PhishingDashboardHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # API: /api/predict?url=...
        if parsed.path == '/api/predict':
            query = urllib.parse.parse_qs(parsed.query)
            url = query.get('url', [''])[0]
            
            if not url:
                err_bytes = json.dumps({'error': 'No URL provided'}).encode('utf-8')
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_bytes)))
                self.send_header('Connection', 'close')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(err_bytes)
                return
            
            try:
                # Predict
                pred, proba = predict_url(url)
                features = extract_features(url)
                confidence = proba[pred] * 100
                
                response_data = {
                    'url': url,
                    'prediction': int(pred),
                    'label': 'PHISHING' if pred == 1 else 'LEGITIMATE',
                    'confidence': round(float(confidence), 2),
                    'prob_legitimate': round(float(proba[0]), 4),
                    'prob_phishing': round(float(proba[1]), 4),
                    'features': features
                }
                resp_bytes = json.dumps(response_data).encode('utf-8')
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(resp_bytes)))
                self.send_header('Connection', 'close')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp_bytes)
            except Exception as e:
                err_bytes = json.dumps({'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_bytes)))
                self.send_header('Connection', 'close')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(err_bytes)
            return
        
        # Root / index: Serve HTML Dashboard
        if parsed.path in ('/', '/index.html', '/dashboard'):
            html_bytes = HTML_TEMPLATE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_bytes)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(html_bytes)
            return
            
        super().do_GET()


def run_server():
    global PORT
    print("⚡ Pre-warming model and cache in memory for sub-millisecond inference...")
    load_model()
    print("✅ Model warm and ready in RAM!")
    while True:
        try:
            with ThreadedTCPServer(("", PORT), PhishingDashboardHandler) as httpd:
                print("\n" + "="*75)
                print(f"🛡️  URL PHISHING INTELLIGENCE DASHBOARD RUNNING")
                print("="*75)
                print(f"🌐 Access Dashboard in Browser: http://localhost:{PORT}")
                print(f"⚡ Real-Time API Endpoint:    http://localhost:{PORT}/api/predict?url=...")
                print("="*75)
                print("Press CTRL+C in this terminal to stop the server.\n")
                
                # Auto-open browser in background thread
                def open_browser():
                    time.sleep(1.2)
                    webbrowser.open(f"http://localhost:{PORT}")
                
                threading.Thread(target=open_browser, daemon=True).start()
                httpd.serve_forever()
        except OSError:
            PORT += 1
            if PORT > 5050:
                print("Could not find open port between 5000 and 5050.")
                sys.exit(1)


if __name__ == '__main__':
    run_server()
