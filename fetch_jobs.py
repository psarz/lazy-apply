import requests
from bs4 import BeautifulSoup
import pandas as pd
import time, random, re

KEYWORDS = '"AWS DevOps" OR "Platform Enablement" OR "Senior DevOps"'
LOCATION = "United States"

def fetch_linkedin_jobs(keywords, location, past_24h=True, max_pages=3):
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36", "Referer": "https://www.linkedin.com/jobs/search"}
    all_jobs=[]
    for page in range(max_pages):
        params={"keywords":keywords,"location":location,"f_TPR":"r86400" if past_24h else "","start":page*25}
        print(f"Fetching page {page+1}/{max_pages}...")
        r=requests.get(base_url, params=params, headers=headers, timeout=15)
        if r.status_code!=200: break
        soup=BeautifulSoup(r.text,"html.parser")
        for card in soup.find_all("li"):
            try:
                title=card.find("h3",class_="base-search-card__title").text.strip()
                company=card.find("h4",class_="base-search-card__subtitle").text.strip()
                loc=card.find("span",class_="job-search-card__location")
                loc=loc.text.strip() if loc else location
                link=card.find("a",class_="base-card__full-link")["href"].split("?")[0]
                job_id=re.search(r"/jobs/view/(\d+)",link).group(1) if re.search(r"/jobs/view/(\d+)",link) else link.split("-")[-1]
                all_jobs.append({"Job ID":job_id,"Title":title,"Company":company,"Location":loc,"URL":link})
            except: continue
        time.sleep(random.uniform(1.5,3.5))
    return pd.DataFrame(all_jobs)

if __name__=="__main__":
    df=fetch_linkedin_jobs(KEYWORDS, LOCATION, past_24h=True, max_pages=3)
    df.to_csv("latest_devops_jobs.csv", index=False)
    print(f"Extracted {len(df)} jobs")
