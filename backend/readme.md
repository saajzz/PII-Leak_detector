# PII Leak Detector — Backend

## Setup

1. Clone the repo
   git clone https://github.com/saajzz/PII-Leak_detector.git

2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt

4. Create `.env` file in `backend/` (or copy `.env.example`)
   - `GITHUB_TOKEN=your_token_here`
   - Add SMTP/Twilio vars if you want live Critical alerts

5. Run Flask API
   python app.py

6. Run pipeline
   python pipeline.py

## Notes

- Scraper now includes: GitHub search, Pastebin, controlc, and paste.fo.
- `alert_system.py` sends email/SMS on Critical incidents when configured.