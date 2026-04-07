# PII Leak Detector — Backend

## Setup

1. Clone the repo
   git clone https://github.com/saajzz/PII-Leak_detector.git

2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt

4. Create .env file in backend/ folder
   GITHUB_TOKEN=your_token_here

5. Run Flask API
   python app.py

6. Run pipeline
   python pipeline.py
