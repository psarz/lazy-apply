cd ~/Documents/autoapply-local

# 1. Make sure venv is active and use its pip, not global pip
source venv/bin/activate
which python
# should show: .../autoapply-local/venv/bin/python

which pip
# should show: .../autoapply-local/venv/bin/pip
# If it shows /usr/local/... you are using global pip - that's the bug

# 2. Install correctly INSIDE venv (use python -m pip, not pip)
python3 -m pip install requests beautifulsoup4 lxml pandas

# OR if venv python is called python3:
# venv/bin/python3 -m pip install requests beautifulsoup4 lxml pandas

# 3. Run with venv's python3, not alias
venv/bin/python3 fetch_jobs.py

# If that works, run Streamlit same way:
venv/bin/python3 -m streamlit run app.py