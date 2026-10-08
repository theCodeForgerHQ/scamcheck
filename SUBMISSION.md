# Devpost submission draft

**Title:** ScamCheck: an AI second opinion before you click
**Tagline:** Paste any suspicious SMS, email or DM and get a risk score, red flags and what to do in seconds.
**Track:** AI + Cybersecurity
**Links:** https://scamcheck.streamlit.app · https://github.com/theCodeForgerHQ/scamcheck · <YouTube link>
**Built with:** python, streamlit, groq, gpt-oss-20b, regex, difflib

## Inspiration
AI has made scam messages fluent and personalised: fake KYC alerts, parcel-fee texts, "part-time job" DMs and lookalike bank links. Victims are often first-time smartphone users and elderly parents, and the moment of risk is the few seconds before they tap a link or share an OTP. We wanted a free, instant second opinion for exactly that moment.

## What it does
You paste a message, and ScamCheck returns:
- a **risk score (0–100)** and a verdict: Safe / Suspicious / Scam
- **red flags**: urgency or threats, OTP or password requests, payment asks, job-scam wording, shortened or raw-IP links, and **lookalike domains** (e.g. `paypa1.com` imitating `paypal.com`, `sbi-kyc-update.in` imitating `sbi.co.in`)
- **what to do next** (don't click, verify through the official app, report at cybercrime.gov.in / 1930)

## How we built it
Two independent signals are blended:
1. **Rule engine.** Regex detectors for common scam tactics, plus lookalike-domain detection that uses `difflib` similarity against ~25 bank, e-commerce, government and courier domains.
2. **LLM analyst.** `gpt-oss-20b` on Groq returns a structured JSON verdict with reasons and advice.

The final score is 40% rules and 60% LLM. If the LLM is unavailable, the app falls back to rules only, so it always gives an answer. The LLM's output is clamped and rendered as plain text, so a malicious message can't inject formatting or links into the result.

## Challenges
- Lookalike detection without false positives on real subdomains (`pay.google.com` must stay safe).
- Getting reliable JSON from the LLM, and staying robust when it fails.
- Treating the analysed message itself as hostile input (prompt injection).

## Accomplishments
- Works end to end and is deployed publicly.
- On our five sample messages it flags all four scams and passes the legitimate one.
- Explanations are understandable to non-technical users.

## What works / what doesn't
**Works:** text analysis, lookalike and short-link detection, AI verdict and advice, rule-only fallback, one-click examples.
**Doesn't yet:** screenshot OCR, voice or call scams, live domain-age/WHOIS lookups. The brand list is hard-coded, and the weights haven't been evaluated on a labelled dataset.

## What's next
Screenshot OCR, a WhatsApp/Telegram bot so users can forward messages directly, WHOIS domain-age checks, and evaluation on a public phishing SMS dataset.

---

# Video script (~2:30)

| Time | On screen | Say |
|---|---|---|
| 0:00 | Title slide or app header | "AI has made scam texts sound real. ScamCheck gives you a second opinion before you click." |
| 0:15 | Pick **Bank KYC** → Check | "A classic fake KYC alert. ScamCheck flags urgency, the OTP request and a lookalike SBI domain, and scores it as a scam." |
| 0:45 | Pick **PayPal lookalike** → Check | "Here the link is paypa1 with a one. Our lookalike detector catches it, and the AI explains why it's phishing." |
| 1:10 | Pick **Job offer** → Check | "Part-time job scams: work-from-home bait plus a shortened link." |
| 1:30 | Pick **Legit** → Check | "And a normal message stays Safe, so it doesn't cry wolf." |
| 1:45 | README architecture diagram | "Two signals: a rule engine for known tactics and lookalike domains, and an LLM on Groq for context. They're blended into one score, with a rules-only fallback." |
| 2:10 | "What doesn't work" section | "Next: screenshot OCR and a WhatsApp bot. Try it at scamcheck.streamlit.app." |
