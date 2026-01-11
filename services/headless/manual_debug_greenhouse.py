import asyncio
import os
import json
from dotenv import load_dotenv
from app.applying.greenhouse import GreenhouseApplier
from app.db import upsert_user, get_user, close_database

# Load environment variables from .env
load_dotenv()

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

    # 4. Job Description
    job_description = """
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

    # 5. Initialize Applier
    # headless=False so we can see the window open/close as requested
    applier = GreenhouseApplier(headless=False)
    
    url = "https://job-boards.greenhouse.io/gorjana/jobs/8369791002"
    
    print(f"\n--- PHASE 1: ANALYSIS ---")
    print(f"Target URL: {url}")
    print("Launching browser to analyze form fields... (Window will close automatically)")
    
    analysis = await applier.analyze_form(
        url, 
        user_profile, 
        job_description=job_description,
        cached_responses={}
    ) # Start fresh or load from DB if needed
    
    if analysis.get("status") == "error":
        print(f"Analysis failed: {analysis.get('message')}")
        return

    print("Analysis complete.")
    fields = analysis.get("fields", [])
    
    # 6. Prompt User for Non-Cached Fields
    print(f"\n--- PHASE 2: REVIEW & INPUT ---")
    print("Reviewing fields. Press Enter to accept Gemini's suggestion.")
    
    for i, field in enumerate(fields):
        print(f"\n[{i+1}/{len(fields)}] Question: {field['label']}")
        print(f"    Type: {field['field_type']}")
        print(f"    Selector: {field.get('selector')}") # Debug info
        
        # Special handling for File fields
        if field['field_type'] == 'file':
            # Check if it's a resume or cover letter based on label or ID
            label_lower = field['label'].lower()
            id_lower = str(field.get('field_id', '')).lower()
            
            if 'resume' in label_lower or 'cv' in label_lower or 'resume' in id_lower:
                field["final_value"] = test_user["resume_path"]
                # Clear recommended_value to prevent fallback to placeholder if path is empty/invalid (though it shouldn't be)
                field["recommended_value"] = None 
                print(f"    Auto-attached Resume: {test_user['resume_path']}")
            else:
                # Cover letter or other - leave empty
                print(f"    Skipping optional file: {field['label']} (ID: {field.get('field_id')})")
                field["final_value"] = ""
                field["recommended_value"] = None # CRITICAL: Prevent fallback to "[Resume will be uploaded]" placeholder
            continue

        source = field.get("source")
        # Skip if confident (Profile or Cached)
        if source in ["cached", "profile"]:
            # Set final value automatically
            field["final_value"] = field.get("recommended_value")
            continue
        
        suggestion = field.get("recommended_value")
        print(f"    Gemini Suggestion: \033[92m{suggestion}\033[0m") # Green text
        
        options = field.get("options")
        if options:
            print("    Options:")
            for idx, opt in enumerate(options):
                print(f"      {idx + 1}) {opt}")
        
        # user_input = input("    > ")
        print("    > (Auto-accepting for debug)")
        
        field["final_value"] = suggestion
        print("    Accepted suggestion.")

    # 7. Apply
    print(f"\n--- PHASE 3: APPLICATION ---")
    print("Launching browser to fill application... (Window will stay open)")
    
    # submit=False to be safe, or True if we want to actually try submitting
    # The prompt implies "do the application", usually means filling it out.
    # We'll set submit=False for safety unless user wants to submit.
    # But usually "do the application" means submit. 
    # However, "manual debug" implies testing.
    # I'll default to False (Dry Run) but keep window open so user can click submit.
    
    result = await applier.fill_and_submit(
        url, 
        fields, 
        user_profile=user_profile,
        job_description=job_description,
        expected_fingerprint=None, # Disable strict check for debug
        submit=False, # User can click submit manually since window stays open
        keep_open=True
    )
    
    print("\nResult:", result)
    await close_database()

if __name__ == "__main__":
    asyncio.run(main())