import asyncio
import json
import os
import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from db import get_db, update_status

async def safe_fill(page, label, text):
    try:
        await page.get_by_label(label, exact=False).first.fill(text, timeout=3000)
        print(f"  ✅ Filled '{label}'")
    except:
        print(f"  ⏭️ Skipped '{label}'")

async def force_dropdown(page, question_part, option_text):
    """Aggressive method to find and click Greenhouse React dropdowns"""
    try:
        # 1. Find the text on the page
        q_element = page.get_by_text(question_part, exact=False).first
        
        # 2. Look for the closest parent container that holds the question
        parent = q_element.locator("xpath=ancestor::div[contains(@class, 'application-question') or contains(@class, 'field') or contains(@class, 'select')]").first
        if await parent.count() == 0:
            parent = q_element.locator("xpath=..").first
            
        # 3. Find the clickable dropdown box inside that container
        dropdown = parent.locator("div[role='combobox'], input[role='combobox'], .select__control").first
        await dropdown.click(timeout=5000)
        await page.wait_for_timeout(1000) # Wait for menu to open
        
        # 4. Click the exact option from the list (using role=option or text)
        option = page.get_by_role("option", name=option_text, exact=True).first
        if await option.count() == 0:
            # Fallback to text search
            option = page.get_by_text(option_text, exact=True).last
        
        await option.click(timeout=5000)
        print(f"  ✅ Selected '{option_text}' for '{question_part[:25]}...'")
        
    except Exception as e:
        print(f"  ⚠️ Failed dropdown '{question_part[:25]}...'")

async def submit_one(job):
    print(f"\n🌐 Opening browser for {job['company']}...")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    Path("screenshots").mkdir(exist_ok=True)
    shot_path = f"screenshots/test_{ts}"
    
    resume_file = "Ayush_Saraswat_resume.pdf" 
    answers = json.loads(job["draft_answers"] or "[]")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        page = await browser.new_page()
        
        try:
            await page.goto(job["url"], timeout=90000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000) 

            print("  -> Filling standard fields...")
            await safe_fill(page, "First Name", "Ayush")
            await safe_fill(page, "Last Name", "Saraswat")
            await safe_fill(page, "Email", "ayushsaraswat861@gmail.com")
            await safe_fill(page, "Phone", "+919555171241")

            print("  -> Filling Location (Google Autocomplete)...")
            try:
                loc = page.get_by_label("Location (City)", exact=False).first
                await loc.click() 
                await loc.fill("Kanpur") 
                await page.wait_for_timeout(2000) 
                suggestion = page.locator(".pac-item").first
                if await suggestion.count() > 0:
                    await suggestion.click()
                    print("  ✅ Location selected from dropdown.")
                else:
                    await loc.press("ArrowDown")
                    await loc.press("Enter")
                    print("  ✅ Location filled via keyboard.")
            except Exception as e:
                print(f"  ⏭️ Location failed.")

            print("  -> Uploading resume...")
            try:
                async with page.expect_file_chooser() as fc_info:
                    await page.get_by_role("button", name="Attach", exact=True).first.click(timeout=5000)
                file_chooser = await fc_info.value
                await file_chooser.set_files(resume_file)
                print("  ✅ Resume uploaded via Attach button.")
            except Exception as e:
                print(f"  ⚠️ Resume upload failed.")

            print("  -> Filling Dropdowns...")
            await force_dropdown(page, "Are you open to working in person", "Yes")
            await force_dropdown(page, "Are you currently bound by any agreements", "No")
            await force_dropdown(page, "Are you legally authorized to work", "Yes")
            await force_dropdown(page, "Will you now or in the future require company sponsorship", "Yes") 

            print("  -> Filling custom text questions...")
            textareas = page.locator("textarea")
            textarea_count = await textareas.count()
            for i, a in enumerate(answers):
                if i < textarea_count:
                    try:
                        await textareas.nth(i).fill(a["answer"], timeout=3000)
                        print(f"  ✅ Filled textarea {i+1}")
                    except:
                        pass

            print("  -> Clicking Submit Button...")
            try:
                # Sometimes the button is disabled, so we force it to wait
                submit_btn = page.get_by_role("button", name="Submit application", exact=False).first
                await submit_btn.click(timeout=5000)
                print("  🚀 Clicked Submit!")
                
                await page.wait_for_timeout(4000) 
                
                # --- HUMAN IN THE LOOP CHECK ---
                page_content = await page.content()
                if "Security code" in page_content or "verification code" in page_content.lower():
                    print("\n" + "="*60)
                    print("🚨 HUMAN VERIFICATION REQUIRED! 🚨")
                    print("Greenhouse sent an OTP code to your email.")
                    print("Please look at the open browser window, type the code, and click Submit.")
                    print("The bot is pausing for 2 minutes to give you time...")
                    print("="*60 + "\n")
                    
                    update_status(get_db(), job["job_id"], "WAITING_FOR_USER")
                    
                    try:
                        # Wait for the thank you page
                        await page.wait_for_selector("text='Thank you'", timeout=120000, state="visible")
                        print("  ✅ User successfully entered the code and submitted!")
                        await page.screenshot(path=f"{shot_path}_submitted.png", full_page=True)
                        update_status(get_db(), job["job_id"], "SUBMITTED", screenshot_path=f"{shot_path}_submitted.png")
                    except Exception:
                        print("  ⚠️ Timed out waiting for you to verify. Moving on.")
                        update_status(get_db(), job["job_id"], "FAILED_VERIFICATION")
                        
                else:
                    if "Thank you" in page_content:
                        print("  ✅ Submitted successfully without verification!")
                        update_status(get_db(), job["job_id"], "SUBMITTED")
                    else:
                        print("  ⚠️ Form submitted, but neither Thank You nor Verification found.")
                        update_status(get_db(), job["job_id"], "SUBMITTED")

            except Exception as e:
                print(f"  ❌ Could not click submit: {e}")

        except Exception as e:
            print(f"  ❌ Major error: {e}")
        finally:
            print("  Closing browser...")
            await browser.close()

async def main():
    con = get_db()
    job = con.execute("SELECT * FROM applications WHERE job_id='freeform_1'").fetchone()
    if job:
        await submit_one(job)

if __name__ == "__main__":
    asyncio.run(main())