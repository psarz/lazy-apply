# AutoApply v3 - One Stop Job Hunt

## What's new in v3?
- **Tab 0: Fetch Latest Jobs** - One-click extractor built into Streamlit (fixes your script). No more ModuleNotFoundError because it runs inside venv.
- Tab 1: Import CSV
- Tab 2: Tailor & Verify (ATS score)
- Tab 3: Auto-Apply (Playwright)

## Install (MacBook Air 7.2 fix included)
```bash
cd autoapply-v3
python3 -m venv venv
source venv/bin/activate
# Use python -m pip, not pip
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m streamlit run app.py
```

## Fix for your "requests" error
Your error: `pip install requests` went to global Python, not venv.
Solution: Always use `python -m pip` inside venv:
```bash
source venv/bin/activate
python -m pip install requests beautifulsoup4 lxml
```

## Usage
1. Open http://localhost:8501
2. Tab 0: Enter keywords like '"AWS DevOps" OR "Platform"' and location, click Fetch
3. Tab 2: Select job, tailor resume, check ATS score
4. Tab 3: Dry run first, then real apply

## Standalone (optional)
python fetch_jobs.py --pages 3

## One-stop flow
Fetch -> Tailor -> PDF -> Apply, all in one app.
