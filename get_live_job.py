import asyncio
from playwright.async_api import async_playwright
from db import get_db

async def get_link():
    print("Searching for a live job URL...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Hidden browser
        page = await browser.new_page()
        await page.goto("https://boards.greenhouse.io/scaleai", timeout=60000)
        
        # Find the first link that points to a job
        link = page.locator("a[href*='/jobs/']").first
        href = await link.get_attribute("href")
        
        # Construct the full URL
        url = f"https://boards.greenhouse.io{href}" if href.startswith("/") else href
        print(f"✅ Found live job: {url}")
        
        con = get_db()
        con.execute('UPDATE applications SET url=? WHERE job_id=?', (url, 'freeform_1'))
        con.commit()
        print("✅ Database updated!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_link())
