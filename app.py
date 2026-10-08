"""ScamCheck: paste a suspicious message, get a risk score, red flags and advice."""
import difflib
import json
import os
import re
from urllib.parse import urlparse

import requests
import streamlit as st

PROVIDERS = {  # env var -> (endpoint, default model); all OpenAI-compatible, all have free tiers
    "GROQ_API_KEY": ("https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-20b"),
    "NVIDIA_API_KEY": ("https://integrate.api.nvidia.com/v1/chat/completions", "nvidia/llama-3.1-nemotron-nano-8b-v1"),
    "FEATHERLESS_API_KEY": ("https://api.featherless.ai/v1/chat/completions", "meta-llama/Meta-Llama-3.1-8B-Instruct"),
}
BRANDS = ["paypal.com", "amazon.com", "google.com", "apple.com", "microsoft.com", "netflix.com",
          "facebook.com", "instagram.com", "whatsapp.com", "sbi.co.in", "hdfcbank.com", "icicibank.com",
          "axisbank.com", "paytm.com", "phonepe.com", "flipkart.com", "irctc.co.in", "incometax.gov.in",
          "indiapost.gov.in", "fedex.com", "dhl.com", "ups.com", "linkedin.com", "chase.com", "wellsfargo.com"]
PATTERNS = {
    "Urgency / threat": r"\b(urgent|immediately|within 24 ?h|suspended|blocked|expire[sd]?|last chance|act now|final notice)\b",
    "Asks for OTP / password": r"\b(otp|one[- ]time password|pin|cvv|password|verify your account|kyc)\b",
    "Money / payment request": r"\b(pay|fee|refund|prize|lottery|won|reward|gift card|crypto|bitcoin|upi|transfer)\b",
    "Too-good job offer": r"\b(work from home|earn \S+ (per|a) day|part[- ]time job|no experience)\b",
    "Shortened link": r"\b(bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|cutt\.ly)\b",
}
EXAMPLES = {
    "Bank KYC": "Dear customer, your SBI account will be BLOCKED today. Update KYC immediately: http://sbi-kyc-update.in/login and share the OTP.",
    "Delivery fee": "IndiaPost: your parcel is on hold due to incomplete address. Pay Rs 25 fee at https://indiapost-gov.co/track within 24h.",
    "Job offer": "Hi! Part-time job, work from home, earn 5000 per day, no experience. WhatsApp me: bit.ly/job-now",
    "PayPal lookalike": "Your PayPal account is suspended. Verify your account at https://paypa1.com/secure",
    "Legit": "Hey, are we still meeting for lunch tomorrow at 1? Let me know.",
}


def rule_check(text: str) -> tuple[int, list[str]]:
    flags = [name for name, pat in PATTERNS.items() if re.search(pat, text, re.I)]
    for url in re.findall(r"(?:https?://)?(?:[\w-]+\.)+[a-z]{2,}(?:/\S*)?", text, re.I):
        host = urlparse(url if "://" in url else "http://" + url).hostname or ""
        host = host.removeprefix("www.")
        if host.replace(".", "").isdigit():
            flags.append(f"Raw IP link: {host}")
        for brand in BRANDS:
            name = brand.split(".")[0]
            ratio = difflib.SequenceMatcher(None, host.split(".")[0], name).ratio()
            if host != brand and not host.endswith("." + brand) and (name in host or ratio > 0.8):
                flags.append(f"Lookalike domain: {host} (imitates {brand})")
                break
    return min(100, 20 * len(flags)), flags


def llm_check(text: str, key: str, url: str, model: str) -> dict:
    prompt = ("You are a fraud analyst. Classify the message below as a scam or not. Reply ONLY with JSON: "
              '{"score": 0-100 scam likelihood, "verdict": "Safe|Suspicious|Scam", '
              '"reasons": [short strings], "advice": "one sentence of what the user should do"}\n\nMessage:\n' + text)
    r = requests.post(url, timeout=60, headers={"Authorization": f"Bearer {key}"},
                      json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0})
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    return json.loads(re.search(r"\{.*\}", content, re.S).group(0))


st.set_page_config(page_title="ScamCheck", page_icon="🛡️")
st.title("🛡️ ScamCheck")
st.caption("Paste a suspicious SMS, email or DM. Rule-based checks plus an LLM give you a verdict.")
def find_provider() -> tuple[str, str, str]:
    for env, (url, model) in PROVIDERS.items():
        try:
            key = os.getenv(env) or st.secrets.get(env, "")
        except Exception:
            key = os.getenv(env, "")
        if key:
            return key, url, model
    return "", "", ""


key, url, model = find_provider()
if not key:
    st.caption("No LLM key configured: running rule-based checks only.")
pick = st.selectbox("Try an example", ["(none)", *EXAMPLES])
text = st.text_area("Message", EXAMPLES.get(pick, ""), height=150)

if st.button("Check", type="primary") and text.strip():
    rule_score, flags = rule_check(text)
    ai = {}
    if key:
        try:
            with st.spinner("Asking the AI analyst..."):
                ai = llm_check(text, key, url, model)
        except Exception as e:
            st.warning(f"AI check unavailable ({type(e).__name__}); showing rule-based result only.")
    score = round(0.4 * rule_score + 0.6 * max(0, min(100, int(ai["score"])))) if "score" in ai else rule_score
    verdict = "Scam" if score >= 60 else "Suspicious" if score >= 30 else "Safe"
    color = {"Scam": "red", "Suspicious": "orange", "Safe": "green"}[verdict]
    st.markdown(f"## :{color}[{verdict}] — risk {score}/100")
    st.progress(score / 100)
    st.subheader("Red flags")
    for f in flags + ai.get("reasons", []):
        st.text("• " + str(f)[:200])
    if not flags and not ai.get("reasons"):
        st.write("None found.")
    st.subheader("What to do")
    st.info(str(ai.get("advice", ""))[:300] or ("Don't click links or share OTPs. Verify through the official app or website, "
                                 "and report fraud at cybercrime.gov.in / 1930." if score >= 30 else "Looks fine. Stay alert."))
