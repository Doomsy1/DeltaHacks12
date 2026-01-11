import asyncio
import os
import json
from dotenv import load_dotenv
from app.applying.greenhouse import GreenhouseApplier
from app.db import upsert_user, get_user, close_database

# Load environment variables from .env
load_dotenv()

URLS = [
    "https://job-boards.greenhouse.io/tlatechinc/jobs/4074977009?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/roo/jobs/5047408008?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/galileofinancialtechnologies/jobs/6517406003?gh_src=my.greenhouse.search",
    "https://job-boards.eu.greenhouse.io/lotusworks/jobs/4746237101?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/redwoodmaterials/jobs/5737879004?gh_jid=5737879004&gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/willowtree/jobs/8364172002?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/grvty/jobs/4091559009?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/sirenopt/jobs/4090525009?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/upwork/jobs/7565868003?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/cartesiansystems/jobs/4076723009?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/dynetherapeutics/jobs/5748627004?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/komodohealth/jobs/8363298002?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/checkr/jobs/7342475?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/checkr/jobs/7342475?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/phizenix/jobs/5058878008?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/atomicmachines/jobs/4093522009?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/remotecom/jobs/7579312003?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/lexingtonmedical/jobs/5057076008?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/formativgroup/jobs/4093476009?gh_src=my.greenhouse.search",
    "https://job-boards.greenhouse.io/atomicmachines/jobs/4092512009?gh_src=my.greenhouse.search",
]

RESULTS_FILE = "manual_test_results.json"

async def main():
    # 0. Ensure Fixtures Exist
    fixtures_dir = os.path.join(os.getcwd(), "tests", "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)
    resume_path = os.path.join(fixtures_dir, "dummy_resume.pdf")
    
    if not os.path.exists(resume_path):
        print(f"Creating dummy resume at {resume_path}...")
        with open(resume_path, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/MediaBox [0 0 595 842]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000111 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n158\n%%EOF")

    # 1. Setup Test Data (Fixture)
    test_user = {
        "email": "alex.smith.temp@example.com",
        "first_name": "Alex",
        "last_name": "Smith",
        "phone": "555-010-9988",
        "location": "New York, NY, USA",
        "linkedin_url": "https://linkedin.com/in/dummy-candidate",
        "website_url": "https://dummy-portfolio.com",
        "github_url": "https://github.com/dummy-candidate",
        "resume_path": resume_path,
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of Technology",
                "year": "2020"
            }
        ],
        "experience": [
             {
                 "company": "TechCorp",
                 "role": "Senior Software Engineer",
                 "duration": "2020 - Present",
                 "description": "Developed scalable backend services using Python and FastAPI. Managed AWS infrastructure."
             }
        ],
        "skills": ["Python", "JavaScript", "TypeScript", "AWS", "Docker", "Kubernetes", "React", "MongoDB"],
        "race": "Prefer not to answer",
        "gender": "Prefer not to answer",
        "veteran_status": "I am not a protected veteran",
        "disability": "I do not have a disability",
        "authorization": "I am authorized to work in this country for any employer",
        "sponsorship": "I do not require sponsorship"
    }
    
    # 2. Upsert User to DB
    print("Upserting test user to MongoDB...")
    await upsert_user(test_user)
    
    # 3. Retrieve User
    user_profile = await get_user(test_user["email"])
    if not user_profile:
        print("Error: Could not retrieve user.")
        return

    # 4. Job Description (Generic Placeholder)
    job_description = ""
    """
    Software Engineer
    
    We are looking for a Software Engineer to join our team.
    
    Requirements:
    - 3+ years of experience with Python and AWS.
    - Experience with Docker and CI/CD.
    - Strong problem solving skills.
    
    Benefits:
    - Competitive salary
    - Remote work
    """

    # Initialize results list
    test_results = []
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r") as f:
                test_results = json.load(f)
        except:
            pass
    
    processed_urls = {res["url"] for res in test_results}

    # 5. Initialize Applier
    applier = GreenhouseApplier(headless=False)
    
    try:
        for idx, url in enumerate(URLS):
            if url in processed_urls:
                print(f"Skipping already processed URL [{idx+1}/{len(URLS)}]: {url}")
                continue

            print(f"\n==================================================")
            print(f"TESTING URL [{idx+1}/{len(URLS)}]: {url}")
            print(f"==================================================")
            
            try:
                print(f"--- PHASE 1: ANALYSIS ---")
                analysis = await applier.analyze_form(
                    url, 
                    user_profile, 
                    job_description=job_description,
                    cached_responses={}
                )
                
                if analysis.get("status") == "error":
                    print(f"Analysis failed: {analysis.get('message')}")
                    # Record failure
                    test_results.append({
                        "url": url,
                        "success": False,
                        "reason": f"Analysis failed: {analysis.get('message')}"
                    })
                    continue

                fields = analysis.get("fields", [])
                
                # Auto-accept all recommendations for speed
                print(f"--- PHASE 2: AUTO-ACCEPTING SUGGESTIONS ---")
                for field in fields:
                    # File handling
                    if field['field_type'] == 'file':
                        label_lower = field['label'].lower()
                        id_lower = str(field.get('field_id', '')).lower()
                        if 'resume' in label_lower or 'cv' in label_lower or 'resume' in id_lower:
                            field["final_value"] = test_user["resume_path"]
                            field["recommended_value"] = None 
                        else:
                            field["final_value"] = ""
                            field["recommended_value"] = None
                        continue

                    # Standard fields
                    source = field.get("source")
                    if source in ["cached", "profile"]:
                        field["final_value"] = field.get("recommended_value")
                        continue
                    
                    suggestion = field.get("recommended_value")
                    field["final_value"] = suggestion

                print(f"--- PHASE 3: FILLING FORM ---")
                # We use a custom call here that waits for user input BEFORE closing
                # Note: fill_and_submit with keep_open=True usually returns immediately but leaves browser open.
                # However, for this test script, we want to pause execution here to let user inspect.
                
                # To achieve "wait for user input then close", we can't rely solely on keep_open=True 
                # because we need to eventually close it to start the next one.
                # So we run fill_and_submit(..., keep_open=True) and then manually close context?
                # No, GreenhouseApplier manages its own context/page in instance variables.
                
                # Actually, GreenhouseApplier.fill_and_submit opens a NEW context/page every time.
                # If keep_open=True, it doesn't close it.
                # We need to access that page or just prompt user, then manually close if possible?
                # The Applier doesn't expose a 'close_last_page' method easily, but we can just let it be.
                # Playwright allows multiple contexts.
                
                result = await applier.fill_and_submit(
                    url, 
                    fields, 
                    user_profile=user_profile,
                    job_description=job_description,
                    expected_fingerprint=None,
                    submit=False,
                    keep_open=True
                )
                
                print("Form filled. Please check the browser window.")
                user_response = input("Did all fields fill correctly? (y/n): ").strip().lower()
                
                success = user_response == 'y'
                notes = ""
                if not success:
                    notes = input("What was wrong? (optional): ").strip()
                
                test_results.append({
                    "url": url,
                    "success": success,
                    "notes": notes
                })

                # Save progress immediately
                with open(RESULTS_FILE, "w") as f:
                    json.dump(test_results, f, indent=2)

                print("Moving to next URL...")
                # We should try to close the page to avoid clutter, 
                # but applier doesn't return the page object directly in fill_and_submit result.
                # Assuming the user manually closes or we rely on OS cleaning up eventually?
                # Ideally we modify Applier or just let it spawn new windows. 
                # For 20 URLs, 20 windows might crash the machine.
                
                # Hack: We can close the browser instance entirely and restart it?
                # Or just accessing applier.browser if it was exposed?
                # Looking at Applier code (not provided fully but usually has self.browser)
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                test_results.append({
                    "url": url,
                    "success": False,
                    "reason": str(e)
                })

    finally:
        await close_database()
        print(f"\nTest complete. Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(main())