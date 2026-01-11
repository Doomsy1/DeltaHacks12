import asyncio
import os
from app.applying.greenhouse import GreenhouseApplier

async def main():
    applier = GreenhouseApplier(headless=False) # See it happening
    
    # Absolute path to dummy resume
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resume_path = os.path.join(current_dir, "tests", "fixtures", "dummy_resume.txt")
    
    candidate = {
        "first_name": "Automated",
        "last_name": "Tester",
        "email": "automated.tester.temp@example.com",
        "phone": "555-0199",
        "resume_path": resume_path,
        "linkedin_url": "https://linkedin.com/in/dummy",
        "website_url": "https://example.com"
    }
    
    url = "https://job-boards.greenhouse.io/gorjana/jobs/8369791002"
    
    print(f"Testing application to {url}")
    print(f"Resume path: {resume_path}")
    
    result = await applier.apply(url, candidate, submit=False)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
