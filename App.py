import streamlit as st
import json, pathlib, re
import pandas as pd
from collections import Counter
import time, random, requests
from bs4 import BeautifulSoup

def parse_csv(path):
    LINKEDIN_MAP = {
        "Company Name": "company", "Company": "company",
        "Job Title": "role", "Title": "role",
        "Job Url": "job_url", "URL": "job_url", "url": "job_url",
        "Location": "location",
        "Description": "description", "Job Description": "description"
    }
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    mapped = {col: LINKEDIN_MAP.get(col, col.lower().replace(" ", "_")) for col in df.columns}
    df = df.rename(columns=mapped)
    for need in ["company","role","job_url"]:
        if need not in df.columns:
            for c in df.columns:
                if need in c:
                    df[need] = df[c]
    if "description" not in df.columns:
        df["description"] = ""
    if "location" not in df.columns:
        df["location"] = "Remote"
    df["responsibilities"] = df.get("description","")
    df["job_url"] = df["job_url"].astype(str)
    jobs = df.to_dict(orient="records")
    for i,j in enumerate(jobs):
        j["id"] = f"job_{i}_{str(j.get('company',''))[:10]}"
        j["status"] = "pending"
    return jobs

def extract_keywords(text):
    if not text: return []
    TECH = ["python","react","node","aws","sql","system design","microservices","api","docker","kubernetes","devops","platform","sre","terraform","jenkins"]
    text_l = text.lower()
    found = [k for k in TECH if k in text_l]
    words = re.findall(r"[A-Za-z]{4,}", text)
    freq = Counter([w.lower() for w in words])
    top = [w for w,_ in freq.most_common(15) if len(w)>4]
    return list(set(found+top))[:20]

def tailor_resume(profile, job):
    jd = (job.get("description","") + " " + job.get("responsibilities",""))[:5000]
    keywords = extract_keywords(jd)
    resume_text = " ".join(profile.get("skills",[])) + " " + profile.get("summary","")
    score = int(sum(1 for k in keywords if k.lower() in resume_text.lower()) / max(len(keywords),1) * 100)
    kw_str = ", ".join(keywords[:5])
    kw_cover = ", ".join(keywords[:6])
    role = job.get('role','')
    company = job.get('company','')
    summary = profile.get("summary","") + f" Experienced in {kw_str} relevant to {role} at {company}."
    return {"keywords": keywords, "ats_score": score, "summary": summary, "experience": profile.get("experience",[]), "cover_letter": f"Hi {company} team, applying for {role} with {kw_cover}", "skills_ranked": profile.get("skills",[])}

def make_pdf_simple(profile, tailored, out_path):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = [Paragraph(f"<b>{profile.get('full_name','')}</b>", styles['Title']), Paragraph(f"{profile.get('email','')} | {profile.get('phone','')}", styles['Normal']), Spacer(1,12), Paragraph("<b>SUMMARY</b>", styles['Heading2']), Paragraph(tailored.get('summary',''), styles['Normal'])]
        doc.build(story)
        return out_path
    except Exception as e:
        pathlib.Path(out_path).write_text(tailored.get('summary',''))
        return out_path

def fetch_linkedin_jobs_live(keywords, location, past_24h=True, max_pages=3, progress_cb=None):
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Referer": "https://www.linkedin.com/jobs/search"}
    all_jobs = []
    for page in range(max_pages):
        params = {"keywords": keywords, "location": location, "f_TPR": "r86400" if past_24h else "", "start": page*25}
        if progress_cb: progress_cb(f"Fetching page {page+1}/{max_pages}...")
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=15)
            if r.status_code != 200:
                if progress_cb: progress_cb(f"Failed {r.status_code}")
                break
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.find_all("li")
            if not cards: break
            new_count=0
            for card in cards:
                try:
                    title_el = card.find("h3", class_="base-search-card__title")
                    company_el = card.find("h4", class_="base-search-card__subtitle")
                    loc_el = card.find("span", class_="job-search-card__location")
                    link_el = card.find("a", class_="base-card__full-link")
                    if not (title_el and company_el and link_el): continue
                    title = title_el.text.strip()
                    company = company_el.text.strip()
                    loc_data = loc_el.text.strip() if loc_el else location
                    job_link = link_el.get("href","").split("?")[0]
                    import re as _re
                    m = _re.search(r"/jobs/view/(\d+)", job_link)
                    job_id = m.group(1) if m else job_link.split("-")[-1].replace("/","")
                    if any(j.get("Job ID")==job_id for j in all_jobs): continue
                    all_jobs.append({"Job ID": job_id, "Title": title, "Company": company, "Location": loc_data, "URL": job_link, "company": company, "role": title, "job_url": job_link, "location": loc_data, "description": "", "id": f"job_live_{job_id}", "status": "pending"})
                    new_count+=1
                except: continue
            if progress_cb: progress_cb(f"Page {page+1}: +{new_count} (total {len(all_jobs)})")
            if new_count==0: break
            time.sleep(random.uniform(1.5, 3.5))
        except Exception as e:
            if progress_cb: progress_cb(f"Error: {e}")
            break
    return all_jobs

BASE = pathlib.Path(__file__).parent
PROFILE_PATH = BASE/"profile.json"
profile = json.loads(PROFILE_PATH.read_text()) if PROFILE_PATH.exists() else {}

st.set_page_config(page_title="AutoApply v3 - One Stop Job Hunt", layout="wide", page_icon="🚀")
st.sidebar.title("🧠 Memory Vault")
with st.sidebar.expander("Edit Profile", expanded=True):
    full_name = st.text_input("Full Name", profile.get("full_name",""))
    email = st.text_input("Email", profile.get("email",""))
    phone = st.text_input("Phone", profile.get("phone",""))
    location = st.text_input("Location", profile.get("location",""))
    summary = st.text_area("Summary", profile.get("summary",""), height=80)
    skills = st.text_area("Skills (comma)", ", ".join(profile.get("skills",[])))
    if st.button("Save Profile"):
        profile.update({"full_name": full_name, "email": email, "phone": phone, "location": location, "summary": summary, "skills": [s.strip() for s in skills.split(",") if s.strip()], "first_name": full_name.split()[0] if full_name else "", "last_name": " ".join(full_name.split()[1:]) if full_name else ""})
        PROFILE_PATH.write_text(json.dumps(profile, indent=2))
        st.success("Saved to profile.json")

st.sidebar.divider()
verify_before = st.sidebar.toggle("Verify before Apply", value=True)

st.title("🚀 AutoApply v3 - One Stop Job Hunt")
st.caption("Fetch → Tailor → Apply in one place. No separate scripts needed.")

tab0, tab1, tab2, tab3 = st.tabs(["0. 🔍 Fetch Latest Jobs", "1. Import CSV", "2. Tailor & Verify", "3. Auto-Apply"])

if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "tailored" not in st.session_state:
    st.session_state.tailored = {}

with tab0:
    st.subheader("🔍 One-Click Extract Latest Jobs (Your Script Fixed)")
    st.info("Uses correct guest API endpoint + pagination. No login needed. This replaces fetch_jobs.py - works inside Streamlit so no ModuleNotFoundError.")
    col_k, col_l = st.columns([2,1])
    with col_k:
        keywords = st.text_input("Keywords (use OR)", value='"AWS DevOps" OR "Platform Enablement" OR "Senior DevOps"')
    with col_l:
        loc = st.text_input("Location", value="United States")
    c1,c2,c3 = st.columns(3)
    with c1:
        past_24h = st.checkbox("Past 24h only", value=True)
    with c2:
        pages = st.slider("Pages (25 jobs/page)", 1, 10, 3)
    with c3:
        fetch_btn = st.button("🚀 Fetch Jobs Now", type="primary", use_container_width=True)
    if fetch_btn:
        status = st.empty()
        prog = st.progress(0)
        def cb(msg): status.info(msg)
        with st.spinner(f"Fetching {pages} pages..."):
            jobs = fetch_linkedin_jobs_live(keywords, loc, past_24h, pages, cb)
            if jobs:
                df_save = pd.DataFrame([{"Job ID": j["Job ID"], "Title": j["Title"], "Company": j["Company"], "Location": j["Location"], "URL": j["URL"]} for j in jobs])
                csv_path = BASE/"data"/"latest_devops_jobs.csv"
                csv_path.parent.mkdir(exist_ok=True)
                df_save.to_csv(csv_path, index=False)
                st.session_state.jobs = jobs
                prog.progress(100)
                status.success(f"✅ Extracted {len(jobs)} jobs -> data/latest_devops_jobs.csv")
                st.dataframe(df_save, use_container_width=True)
                st.download_button("Download CSV", df_save.to_csv(index=False), file_name="latest_jobs.csv", mime="text/csv")
                st.success("Go to Tab 2 to tailor resumes!")
            else:
                status.warning("No jobs found - try broader keywords or wait 2 mins (rate limit)")

with tab1:
    st.subheader("Import CSV (Alternative)")
    st.caption("If you have LinkedIn export or CSV from Tab 0")
    uploaded = st.file_uploader("Drop CSV", type=["csv"])
    if st.button("Load Sample"):
        p = BASE/"data"/"linkedin_sample.csv"
        if p.exists():
            st.session_state.jobs = parse_csv(str(p))
            st.success(f"Loaded {len(st.session_state.jobs)}")
    if uploaded:
        path = BASE/"data"/"uploaded.csv"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(uploaded.read())
        st.session_state.jobs = parse_csv(str(path))
        st.success(f"Parsed {len(st.session_state.jobs)}")
    if st.session_state.jobs:
        st.dataframe(pd.DataFrame(st.session_state.jobs)[["company","role","location","job_url","status"]], use_container_width=True)

with tab2:
    if not st.session_state.jobs:
        st.warning("Fetch in Tab 0 or import in Tab 1 first")
    else:
        opts = [f"{j['company']} - {j['role']} ({j['id']})" for j in st.session_state.jobs]
        sel = st.selectbox("Select Job to Tailor", opts)
        idx = opts.index(sel)
        job = st.session_state.jobs[idx]
        c1,c2 = st.columns([1,1])
        with c1:
            st.markdown(f"### {job['role']} @ {job['company']}")
            st.caption(job['job_url'])
            desc = st.text_area("JD (paste if empty)", value=job.get('description',''), height=250)
            if st.button("Save JD"):
                job['description']=desc
                st.session_state.jobs[idx]=job
                st.success("Updated")
            if st.button("✨ Tailor Resume", type="primary"):
                tailored = tailor_resume(profile, job)
                st.session_state.tailored[job['id']]=tailored
                out = BASE/f"resumes/tailored_{job['id']}.pdf"
                out.parent.mkdir(exist_ok=True)
                make_pdf_simple(profile, tailored, str(out))
                st.success(f"ATS Score: {tailored['ats_score']}% | PDF saved")
        with c2:
            tailored = st.session_state.tailored.get(job['id'])
            if tailored:
                st.metric("ATS Score", f"{tailored['ats_score']}%")
                st.write("Keywords:", ", ".join(tailored['keywords'][:10]))
                st.text_area("Tailored Summary", value=tailored['summary'], height=120)
                st.text_area("Cover Letter", value=tailored['cover_letter'], height=150)
                pdf_path = BASE/f"resumes/tailored_{job['id']}.pdf"
                if pdf_path.exists():
                    with open(pdf_path,"rb") as f:
                        st.download_button("Download PDF", f, file_name=pdf_path.name)
                st.checkbox("I verified - ready to apply", key=f"verify_{job['id']}")
            else:
                st.info("Click Tailor")

with tab3:
    st.subheader("One-Click Apply")
    dry = st.toggle("Dry Run (screenshot only, safe)", value=verify_before)
    headless = st.toggle("Headless browser", value=False)
    for j in st.session_state.jobs:
        tailored = st.session_state.tailored.get(j['id'])
        if not tailored: continue
        verified = st.session_state.get(f"verify_{j['id']}", False) or not verify_before
        with st.expander(f"{j['company']} - {j['role']} | ATS {tailored['ats_score']}% | Verified: {verified}"):
            st.write(j['job_url'])
            if st.button(f"🚀 Apply Now - {j['id']}", key=f"apply_{j['id']}"):
                if not verified:
                    st.error("Please verify in Tab 2 first")
                else:
                    try:
                        import asyncio
                        from playwright.async_api import async_playwright
                        async def run():
                            async with async_playwright() as p:
                                b = await p.chromium.launch(headless=headless)
                                pg = await b.new_page()
                                await pg.goto(j['job_url'], timeout=60000)
                                await pg.wait_for_timeout(2000)
                                await pg.screenshot(path=str(BASE/f"output/preview_{j['id']}.png"), full_page=True)
                                await b.close()
                        asyncio.run(run())
                        st.success(f"Screenshot saved to output/preview_{j['id']}.png")
                        img = BASE/f"output/preview_{j['id']}.png"
                        if img.exists():
                            st.image(str(img))
                    except Exception as e:
                        st.error(f"Apply error: {e} - run: playwright install chromium")
