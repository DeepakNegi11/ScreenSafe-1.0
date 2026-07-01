# backend/sensitive_detector.py

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np

# ─────────────────────────────────────────────
# REGEX PATTERNS for structured sensitive data
# ─────────────────────────────────────────────
PATTERNS = {
    "OTP": [
        r'\bOTP[:\s]*\d{4,8}\b',
        r'\bone[- ]?time[- ]?password[:\s]*\d{4,8}\b',
        r'\bverification[- ]?code[:\s]*\d{4,8}\b',
        r'\b\d{6}\b(?=.*(?:otp|code|verify|auth))',   # 6-digit near trigger word
    ],
    "Credit/Debit Card": [
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?)\b',           # Visa
        r'\b(?:5[1-5][0-9]{14})\b',                    # MasterCard
        r'\b(?:3[47][0-9]{13})\b',                     # American Express
        r'\b(?:\d{4}[- ]){3}\d{4}\b',                 # Generic formatted card
    ],
    "CVV": [
        r'\bCVV[:\s]*\d{3,4}\b',
        r'\bCVC[:\s]*\d{3,4}\b',
        r'\bsecurity[- ]?code[:\s]*\d{3,4}\b',
    ],
    "Password": [
        r'\bpassword[:\s]+\S+',
        r'\bpasswd[:\s]+\S+',
        r'\bpwd[:\s]+\S+',
        r'\bpin[:\s]*\d{4,6}\b',
    ],
    "Email": [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ],
    "Phone Number": [
        r'\b(?:\+91[\-\s]?)?[6-9]\d{9}\b',            # Indian mobile
        r'\b\+?[1-9]\d{1,14}\b',                       # International
        r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',         # US format
    ],
    "Bank Account": [
        r'\baccount[:\s#]*\d{9,18}\b',
        r'\bIFSC[:\s]*[A-Z]{4}0[A-Z0-9]{6}\b',
        r'\bIBAN[:\s]*[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',
    ],
    "Aadhaar (India)": [
        r'\b\d{4}\s\d{4}\s\d{4}\b',
        r'\baadhaar[:\s]*\d{12}\b',
    ],
    "PAN Card (India)": [
        r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
    ],
    "Private Key / Token": [
        r'\bsk-[a-zA-Z0-9]{20,}\b',                   # OpenAI / API keys
        r'\bghp_[a-zA-Z0-9]{36}\b',                   # GitHub token
        r'\bxox[baprs]-[0-9A-Za-z]{10,48}\b',         # Slack token
        r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
    ],
    "Social Security Number": [
        r'\b\d{3}-\d{2}-\d{4}\b',
    ],
}

# ─────────────────────────────────────────────
# ML CLASSIFIER (Naive Bayes on TF-IDF)
# Trained on simple examples to catch contextual leaks
# ─────────────────────────────────────────────

TRAINING_DATA = [
    # Sensitive examples
    ("your otp is 482910 do not share", "sensitive"),
    ("password: MySecret123", "sensitive"),
    ("card number 4111 1111 1111 1111", "sensitive"),
    ("cvv 234 expiry 12/26", "sensitive"),
    ("enter your pin 4829", "sensitive"),
    ("bank account 9876543210 ifsc HDFC0001234", "sensitive"),
    ("aadhaar 1234 5678 9012", "sensitive"),
    ("api key sk-abc123def456ghi789", "sensitive"),
    ("private key -----BEGIN RSA PRIVATE KEY-----", "sensitive"),
    ("ssn 123-45-6789", "sensitive"),
    ("verification code 102938", "sensitive"),
    ("login credentials username admin password root", "sensitive"),
    # Non-sensitive examples
    ("hello how are you today", "safe"),
    ("the weather is nice outside", "safe"),
    ("let us schedule a meeting for tomorrow", "safe"),
    ("please find the report attached", "safe"),
    ("open the project in visual studio code", "safe"),
    ("the server is running on port 3000", "safe"),
    ("good morning team sync at 10am", "safe"),
    ("the presentation is ready for review", "safe"),
]

def train_ml_model():
    texts = [t for t, _ in TRAINING_DATA]
    labels = [l for _, l in TRAINING_DATA]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X = vectorizer.fit_transform(texts)
    model = MultinomialNB()
    model.fit(X, labels)
    return vectorizer, model

# Train once at import time
_vectorizer, _model = train_ml_model()

def ml_classify(text):
    """Uses the trained ML model to classify a text chunk."""
    X = _vectorizer.transform([text.lower()])
    prediction = _model.predict(X)[0]
    proba = _model.predict_proba(X)[0]
    classes = _model.classes_
    confidence = dict(zip(classes, proba))
    return prediction, confidence

def detect_sensitive_data(text):
    """
    Main detection function.
    Combines Regex + ML to find sensitive data in extracted screen text.
    
    Returns:
    {
        "is_sensitive": True/False,
        "findings": [
            {"type": "OTP", "match": "482910", "method": "regex"},
            {"type": "contextual", "match": "...", "method": "ml", "confidence": 0.87}
        ],
        "risk_level": "HIGH" / "MEDIUM" / "LOW"
    }
    """
    findings = []
    
    # ── Step 1: Regex scan ──
    for data_type, pattern_list in PATTERNS.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": data_type,
                    "match": match[:50],   # truncate for safety
                    "method": "regex"
                })
    
    # ── Step 2: ML scan on 200-char sliding windows ──
    window_size = 200
    step = 100
    for i in range(0, max(1, len(text) - window_size), step):
        chunk = text[i:i + window_size]
        if len(chunk.strip()) < 10:
            continue
        prediction, confidence = ml_classify(chunk)
        if prediction == "sensitive" and confidence.get("sensitive", 0) > 0.75:
            findings.append({
                "type": "contextual_leak",
                "match": chunk[:80] + "...",
                "method": "ml",
                "confidence": round(confidence["sensitive"], 2)
            })
    
    # ── Step 3: Risk level ──
    high_risk_types = {"OTP", "Credit/Debit Card", "Password", "CVV",
                       "Bank Account", "Private Key / Token", "Aadhaar (India)"}
    is_sensitive = len(findings) > 0
    risk_level = "LOW"
    if any(f["type"] in high_risk_types for f in findings):
        risk_level = "HIGH"
    elif is_sensitive:
        risk_level = "MEDIUM"
    
    return {
        "is_sensitive": is_sensitive,
        "findings": findings,
        "risk_level": risk_level
    }


if __name__ == "__main__":
    test = "Your OTP is 482910. Do not share with anyone. Card: 4111 1111 1111 1111"
    print(detect_sensitive_data(test))