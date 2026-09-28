
import asyncio
from playwright.async_api import async_playwright
import pathlib, json

# Map profile fields to common ATS selectors
SELECTORS = {
    "first_name": ["input[name*=first]", "input[autocomplete=given-name]"],
    "last_name": ["input[name*=last]", "input[autocomplete=family-name]"],
    "email": ["input[type=email]", "input[name*=email]"],
    "phone": ["input[type=tel]", "input[name*=phone]"],
    "linkedin": ["input[name*=linkedin]"],
    "location": ["input[name*=location]", "input[name*=city]"],
    "portfolio": ["input[name*=portfolio]", "input[name*=website]"],
}

async def fill_form(page, profile):
    for field, sels in SELECTORS.items():
        val = profile.get(field) or profile.get("full_name","").split()[0] if field=="first_name" else profile.get(field)
        if not val: 
            if field=="first_name": val = profile.get("full_name","").split()[0]
            elif field=="last_name": val = " ".join(profile.get("full_name","").split()[1:])
            else: continue
        for sel in sels:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(str(val), timeout=2000)
                    break
            except: pass

async def apply_to_job(job, profile, tailored_resume_path, headless=False, dry_run=True):
    # dry_run = True means it will fill but NOT submit - for verification
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(job["job_url"], wait_until="domcontentloaded", timeout=60000)
        # Basic detection
        url = job["job_url"]
        if "linkedin.com" in url:
            # LinkedIn Easy Apply - needs login
            # We assume user is already logged in via persistent context - for demo we pause
            print(f"[LinkedIn] Opening {url} - user must be logged in. Easy Apply steps will be guided.")
            # Try to click Easy Apply
            try:
                await page.get_by_role("button", name="Easy Apply").click(timeout=5000)
                await page.wait_for_timeout(2000)
                await fill_form(page, profile)
                # Upload resume if file input found
                file_inputs = page.locator("input[type=file]")
                if await file_inputs.count()>0 and tailored_resume_path:
                    await file_inputs.first.set_input_files(str(tailored_resume_path))
                if not dry_run:
                    # Click next/submit loops - simplified
                    for _ in range(5):
                        next_btn = page.get_by_role("button", name="Continue")
                        if await next_btn.count()==0:
                            next_btn = page.get_by_role("button", name="Next")
                        if await next_btn.count()>0:
                            await next_btn.click()
                            await page.wait_for_timeout(1500)
                        else:
                            break
                    submit = page.get_by_role("button", name="Submit application")
                    if await submit.count()>0 and not dry_run:
                        await submit.click()
                        print("Submitted!")
            except Exception as e:
                print(f"LinkedIn flow error (expected in dry run): {e}")
                await page.pause() if not headless else await page.wait_for_timeout(5000)
        else:
            # Generic Greenhouse / Lever / Ashby
            await fill_form(page, profile)
            if not dry_run:
                print("Filled generic ATS - ready to submit (manual check).")
            await page.wait_for_timeout(3000)
        if dry_run:
            await page.screenshot(path=f"output/preview_{job['id']}.png", full_page=True)
        await browser.close()
        return True
