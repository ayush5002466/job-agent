import asyncio
import json
import os
import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from db import get_db, update_status
from otp_reader import get_otp

async def safe_fill(page, label, text):
    try:
        await page.get_by_label(label, exact=False).first.fill(text, timeout=3000)
        print(f"  ✅ Filled '{label}'")
    except:
        print(f"  ⏭️ Skipped '{label}'")

async def force_dropdown(page, question_part, option_text):
    try:
        q_element = page.get_by_text(question_part, exact=False).first
        parent = q_element.locator("xpath=ancestor::div[contains(@class, 'application-question') or contains(@class, 'field')]").first
        if await parent.count() == 0:
            parent = q_element.locator("xpath=..").first
        dropdown = parent.locator("div[role='combobox'], input[role='combobox']").first
        await dropdown.click(timeout=5000)
        await page.wait_for_timeout(800) 
        await page.keyboard.type(option_text, delay=100)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
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

            print("  -> Filling Location...")
            try:
                loc = page.get_by_label("Location (City)", exact=False).first
                await loc.click() 
                await loc.fill("Kanpur") 
                await page.wait_for_timeout(2000) 
                suggestion = page.locator(".pac-item").first
                if await suggestion.count() > 0:
                    await suggestion.click()
                    print("  ✅ Location selected.")
                else:
                    await loc.press("ArrowDown")
                    await loc.press("Enter")
                    print("  ✅ Location filled.")
            except Exception:
                print(f"  ⏭️ Location skipped.")

            print("  -> Uploading resume...")
            try:
                async with page.expect_file_chooser() as fc_info:
                    await page.get_by_role("button", name="Attach", exact=True).first.click(timeout=5000)
                file_chooser = await fc_info.value
                await file_chooser.set_files(resume_file)
                print("  ✅ Resume uploaded.")
            except Exception:
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
                    except:
                        pass

            print("  -> Clicking Submit Button...")
            try:
                submit_btn = page.get_by_role("button", name="Submit application", exact=False).first
                await submit_btn.click(timeout=5000)
                print("  🚀 Clicked Submit!")
                
                await page.wait_for_timeout(4000) 
                page_content = await page.content()
                
                if "Security code" in page_content or "verification code" in page_content.lower():
                    print("\n🚨 OTP REQUIRED! Fetching from Gmail...")
                    otp_code = get_otp()
                    
                    if otp_code:
                        print(f"  ✅ Found OTP: {otp_code}")
                        # Fill the 8 boxes
                        inputs = page.locator("input[type='text'], input[type='tel']")
                        for i, char in enumerate(otp_code):
                            if i < await inputs.count():
                                await inputs.nth(i).fill(char)
                                await page.wait_for_timeout(100)
                        
                        # Click submit again
                        await page.get_by_role("button", name="Submit application", exact=False).first.click()
                        await page.wait_for_timeout(5000)
                        print("  🚀 Submitted OTP!")
                    else:
                        print("  ❌ Could not fetch OTP.")
                        update_status(get_db(), job["job_id"], "FAILED_OTP")
                        return

                # Check if success
                page_content = await page.content()
                if "Thank you" in page_content or "application has been submitted" in page_content.lower():
                    print("  ✅ Submitted successfully!")
                    await page.screenshot(path=f"{shot_path}_submitted.png", full_page=True)
                    update_status(get_db(), job["job_id"], "SUBMITTED", screenshot_path=f"{shot_path}_submitted.png")
                else:
                    print("  ⚠️ Could not confirm success. Check screenshot.")
                    await page.screenshot(path=f"{shot_path}_unknown.png", full_page=True)
                    update_status(get_db(), job["job_id"], "UNKNOWN")
                    
            except Exception as e:
                print(f"  ❌ Could not click submit: {e}")

        except Exception as e:
            print(f"  ❌ Major error: {e}")
        finally:
            await browser.close()

async def main():
    con = get_db()
    job = con.execute("SELECT * FROM applications WHERE status='AWAITING_APPROVAL' LIMIT 1").fetchone()
    if job:
        await submit_one(job)

if __name__ == "__main__":
    asyncio.run(main())
