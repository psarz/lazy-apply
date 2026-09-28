
import pandas as pd
import re

LINKEDIN_MAP = {
    "Company Name": "company", "Company": "company", "#company": "company",
    "Job Title": "role", "Title": "role", "#job_title": "role",
    "Job Url": "job_url", "LinkedIn Link": "job_url", "url": "job_url", "Link": "job_url", "apply_url": "job_url", "#apply_url": "job_url",
    "Location": "location", "#city": "location", "City": "location", "#location": "location",
    "Description": "description", "Job Description": "description", "#job_description": "description", "summary": "description", "JD": "description",
    "Saved Date": "saved_date", "Captured At": "saved_date"
}

def parse_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # normalize
    mapped = {}
    for col in df.columns:
        mapped[col] = LINKEDIN_MAP.get(col, col.lower().replace(" ", "_"))
    df = df.rename(columns=mapped)
    # ensure required
    for need in ["company","role","job_url"]:
        if need not in df.columns:
            # try fuzzy
            for c in df.columns:
                if need in c: 
                    df[need] = df[c]
    if "description" not in df.columns:
        df["description"] = ""
    if "location" not in df.columns:
        df["location"] = "Remote"
    df["responsibilities"] = df.get("description","")
    df["job_url"] = df["job_url"].astype(str)
    # clean
    jobs = df.to_dict(orient="records")
    for i,j in enumerate(jobs):
        j["id"] = f"job_{i}_{j.get('company','')[:10]}"
        j["status"] = "pending"
    return jobs
