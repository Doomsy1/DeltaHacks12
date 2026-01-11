import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://job-boards.greenhouse.io/gorjana/jobs/8369791002"
        print(f"Navigating to {url}")
        await page.goto(url)
        
        # Wait for form
        try:
            await page.wait_for_selector("form", timeout=5000)
            print("Form found.")
        except:
            print("Form not found immediately.")

        # Dump inputs
        inputs = await page.query_selector_all("input")
        print(f"Found {len(inputs)} inputs.")
        for i in inputs:
            id_attr = await i.get_attribute("id")
            name_attr = await i.get_attribute("name")
            type_attr = await i.get_attribute("type")
            print(f"Input: id={id_attr}, name={name_attr}, type={type_attr}")

        # Check for resume upload
        file_inputs = await page.query_selector_all("input[type='file']")
        print(f"Found {len(file_inputs)} file inputs.")
        for f in file_inputs:
            id_attr = await f.get_attribute("id")
            print(f"File Input: id={id_attr}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
