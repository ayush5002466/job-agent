import asyncio
import json
import os
import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from db import get_db, update_status

async def fill_dropdown(page, label, option_text):
    """Helper to handle Greenhouse's React-Select dropdowns"""
    try:
        # Find the input associated with the label
        inp = page.get_by_label(label, exact=False).first
        await inp.click()
        await page.wait_for_timeout(500) # Wait for menu to open
        # Click the option text
        await page.get_by_text(option_text, exact=True).first.click()
        print(f"  ✅ Selected '{option_text}' for '{label}'")
        await page.wait_for_timeout(300)
    except Exception as e:
        print(f"  ⚠️ Could not fill dropdown '{label}': {e}")

async def submit_one(job):
    print(f"\n🌐 Opening browser for {job['company']}...")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("screenshots").mkdir(exist_ok=True)
    shot_path = f"screenshots/Freeform_{ts}"
    
    answers = json.loads(job["draft_answers"] or "[]")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
        
        try:
            await page.goto(job["url"], timeout=60000)
            await page.wait_for_timeout(3000) 

            print("  -> Filling standard fields...")
            await page.get_by_label("First Name", exact=False).first.fill("Ayush")
            await page.get_by_label("Last Name", exact=False).first.fill("Saraswat")
            await page.get_by_label("Email", exact=False).first.fill("ayushsaraswat861@gmail.com")
            await page.get_by_label("Location", exact=False).first.fill("Kanpur, India")
            await page.get_by_label("Phone", exact=False).first.fill("+91XXXXXXXXXX") # UPDATE THIS

            print("  -> Uploading resume...")
            file_inputs = page.locator("input[type='file']")
            if await file_inputs.count() > 0:
                if os.path.exists("Ayush_Saraswat_Resume_Final.pdf"):
                    await file_inputs.first.set_input_files("Ayush_Saraswat_Resume_Final.pdf")
                    print("  ✅ Resume uploaded.")

            print("  -> Filling Education...")
            # The text field for School
            await page.get_by_label("School", exact=False).first.fill("PSIT, AKTU")
            # React-Select Dropdowns for Education
            await fill_dropdown(page, "Degree", "Bachelor's Degree")
            await fill_dropdown(page, "Discipline", "Computer Science")
            await fill_dropdown(page, "End date month", "May") # Adjust as needed
            # End date year is usually a text field in this specific form
            try:
                await page.get_by_label("End date year", exact=False).first.fill("2028")
            except:
                pass

            print("  -> Filling custom dropdowns...")
            await fill_dropdown(page, "How did you hear about us?", "LinkedIn") # Or "Other"
            await fill_dropdown(page, "What month will you be able to start your internship?", "June")
            await fill_dropdown(page, "GPA (Undergraduate)", "8.0") # Adjust to your actual GPA
            await fill_dropdown(page, "What is your strongest coding language?", "Java")
            await fill_dropdown(page, "Are you open to working onsite 5 days a week?", "Yes")
            await fill_dropdown(page, "Are you currently based in the Los Angeles area or willing to relocate to the Los Angeles area?", "Yes")
            
            print("  -> Filling Citizenship...")
            await fill_dropdown(page, "Citizenship Status", "Other")
            # If "Other", explain box
            other_explain = page.get_by_label("If \"Other\", please explain", exact=False)
            if await other_explain.count() > 0:
                await other_explain.first.fill("Indian citizen. I will require visa sponsorship to work in the US.")

            print("  -> Filling custom text questions...")
            textareas = page.locator("textarea")
            textarea_count = await textareas.count()
            for i, a in enumerate(answers):
                if i < textarea_count:
                    await textareas.nth(i).fill(a["answer"])
                    await page.wait_for_timeout(500)

            # Screenshot BEFORE submit
            await page.screenshot(path=f"{shot_path}_filled.png", full_page=True)
            print(f"  📸 Saved screenshot: {shot_path}_filled.png")

            print("  ✅ Filled form successfully. (Submit is disabled for testing).")
            update_status(get_db(), job["job_id"], "FILLED_TEST", screenshot_path=f"{shot_path}_filled.png")

        except Exception as e:
            print(f"  ❌ Failed to fill form: {e}")
        finally:
            print("  Closing browser in 15 seconds so you can look at it...")
            await page.wait_for_timeout(15000)
            await browser.close()

async def main():
    con = get_db()
    # Look for the Freeform job specifically
    job = con.execute("SELECT * FROM applications WHERE job_id='freeform_1'").fetchone()
    if job:
        await submit_one(job)
    else:
        print("Freeform job not found in database.")

if __name__ == "__main__":
    asyncio.run(main())
