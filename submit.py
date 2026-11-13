import asyncio
import json
import os
import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from db import get_db, update_status

async def fill_dropdown(page, label_text, option_text):
    """Helper function to click a custom dropdown and select an option"""
    try:
        # Find the dropdown by its label (e.g., "Degree")
        label = page.get_by_text(label_text, exact=True).first
        parent = label.locator("xpath=..")
        
        # Click the input box associated with it
        input_box = parent.locator("input[role='combobox'], select, [role='button']").first
        await input_box.click()
        await page.wait_for_timeout(500) # Wait for animation
        
        # Click the option
        await page.get_by_text(option_text, exact=True).first.click()
        await page.wait_for_timeout(500)
        print(f"  ✅ Selected '{option_text}' for '{label_text}'")
    except Exception as e:
        print(f"  ⚠️ Could not fill dropdown {label_text}: {e}")

async def submit_one(job):
    print(f"\n🌐 Opening browser for {job['company']}...")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("screenshots").mkdir(exist_ok=True)
    shot_path = f"screenshots/{job['company'].replace(' ', '_')}_{ts}"
    
    answers = json.loads(job["draft_answers"] or "[]")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Set to True later
        page = await browser.new_page()
        
        try:
            if not job["url"] or job["url"] == "PASTE_PUBLIC_URL_HERE":
                print("❌ ERROR: You need to replace 'PASTE_PUBLIC_URL_HERE' with the real job URL in the database.")
                return

            await page.goto(job["url"], timeout=60000)
            await page.wait_for_timeout(3000) 

            print("  -> Filling standard fields...")
            # Note: Greenhouse usually pre-fills name/email if you are logged in, but we do it anyway
            try:
                await page.get_by_label("First Name", exact=False).first.fill("Ayush", timeout=2000)
                await page.get_by_label("Last Name", exact=False).first.fill("Saraswat", timeout=2000)
                await page.get_by_label("Email", exact=False).first.fill("ayushsaraswat861@gmail.com", timeout=2000)
                await page.get_by_label("Phone", exact=False).first.fill("+91XXXXXXXXXX", timeout=2000) # UPDATE THIS
                await page.get_by_label("Location", exact=False).first.fill("Kanpur, India", timeout=2000)
            except Exception:
                print("  -> Some standard fields might be pre-filled.")

            print("  -> Uploading resume...")
            file_inputs = page.locator("input[type='file']")
            if await file_inputs.count() > 0:
                if os.path.exists("Ayush_Saraswat_Resume_Final.pdf"):
                    await file_inputs.first.set_input_files("Ayush_Saraswat_Resume_Final.pdf")
                    print("  ✅ Resume uploaded.")
                else:
                    print("  ⚠️ WARNING: Ayush_Saraswat_Resume_Final.pdf not found!")

            print("  -> Trying to fill dropdowns...")
            await fill_dropdown(page, "Degree", "Bachelor's Degree")
            await fill_dropdown(page, "Discipline", "Computer Science")
            await fill_dropdown(page, "End date year", "2028")
            await fill_dropdown(page, "Are you open to working onsite 5 days a week?", "Yes")
            await fill_dropdown(page, "Are you currently based in the Los Angeles area or willing to relocate to the Los Angeles area?", "Yes")
            await fill_dropdown(page, "Citizenship Status", "Other") # Or whichever applies

            print("  -> Filling custom questions...")
            textareas = page.locator("textarea")
            textarea_count = await textareas.count()
            for i, a in enumerate(answers):
                if i < textarea_count:
                    await textareas.nth(i).fill(a["answer"])
                    await page.wait_for_timeout(500)

            # Screenshot BEFORE submit
            await page.screenshot(path=f"{shot_path}_filled.png", full_page=True)
            print(f"  📸 Saved filled form screenshot: {shot_path}_filled.png")

            print("  ✅ Filled form successfully. (Submit is disabled for testing).")
            update_status(get_db(), job["job_id"], "FILLED_TEST", screenshot_path=f"{shot_path}_filled.png")

        except Exception as e:
            print(f"  ❌ Failed to fill form: {e}")
            update_status(get_db(), job["job_id"], "FAILED")
        finally:
            print("  Closing browser in 10 seconds so you can look at it...")
            await page.wait_for_timeout(10000)
            await browser.close()

async def submit_approved():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='AWAITING_APPROVAL'").fetchall()
    for job in jobs:
        await submit_one(job)

if __name__ == "__main__":
    asyncio.run(submit_approved())
