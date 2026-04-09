import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://esupply.dubai.gov.ae/esop/guest/go/public/opportunity/current")
        print(await page.title())
        content = await page.content()
        print("Tenders found:", "Opportunity" in content and "Tender" in content)
        await browser.close()
asyncio.run(run())
