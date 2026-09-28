import re, json
from collections import Counter

def extract_keywords(text):
    if not text: return []
    TECH = ["python","react","node","aws","sql","system design","microservices","api","docker","kubernetes","typescript","java","golang","product","lead","latency","scalability"]
    text_l = text.lower()
    found = [k for k in TECH if k in text_l]
    words = re.findall(r"[A-Za-z]{4,}", text)
    freq = Counter([w.lower() for w in words])
    top = [w for w,_ in freq.most_common(15) if len(w)>4]
    return list(set(found+top))[:20]

def tailor_resume(profile, job):
    jd = (job.get("description","") + " " + job.get("responsibilities",""))[:5000]
    keywords = extract_keywords(jd)
    
    resume_text = " ".join(profile.get("skills",[])) + " " + profile.get("summary","") + " " + " ".join([b for exp in profile.get("experience",[]) for b in exp.get("bullets",[])])
    resume_text_l = resume_text.lower()
    score = int(sum(1 for k in keywords if k.lower() in resume_text_l) / max(len(keywords),1) * 100)
    
    # Fixed f-string - avoid nested quotes
    kw_str = ", ".join(keywords[:5])
    role = job.get('role','')
    company = job.get('company','')
    tailored_summary = profile.get("summary","") + f" Experienced in {kw_str} relevant to {role} at {company}."
    
    tailored_exp = []
    for exp in profile.get("experience",[]):
        scored_bullets = []
        for b in exp.get("bullets",[]):
            match = sum(1 for k in keywords if k.lower() in b.lower())
            scored_bullets.append((match,b))
        scored_bullets.sort(reverse=True, key=lambda x: x[0])
        tailored_exp.append({**exp, "bullets": [b for _,b in scored_bullets]})
    
    kw_cover = ", ".join(keywords[:6])
    jd_snip = jd[:300]
    full_name = profile.get('full_name','')
    first_exp_title = profile.get('experience',[{}])[0].get('title','experience') if profile.get('experience') else 'experience'
    cover = f"Hi {company} team,\n\nI am excited to apply for {role}. My experience in {kw_cover} aligns with your requirements: {jd_snip}... I have {first_exp_title} building scalable products.\n\nRegards, {full_name}"
    
    ranked = sorted(profile.get("skills",[]), key=lambda s: 0 if s.lower() in [k.lower() for k in keywords] else 1)
    
    return {
        "keywords": keywords,
        "ats_score": score,
        "summary": tailored_summary,
        "experience": tailored_exp,
        "cover_letter": cover,
        "skills_ranked": ranked
    }
