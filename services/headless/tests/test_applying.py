import pytest
import os
import asyncio
from app.applying.greenhouse import GreenhouseApplier

@pytest.mark.asyncio
async def test_apply_dry_run():
    # Setup paths
    current_dir = os.path.dirname(__file__)
    fixtures_dir = os.path.join(current_dir, "fixtures")
    html_path = os.path.join(fixtures_dir, "greenhouse_job.html")
    resume_path = os.path.join(fixtures_dir, "dummy_resume.txt")
    
    # Ensure fixtures exist
    if not os.path.exists(html_path):
        pytest.fail(f"HTML fixture not found at {html_path}")
    if not os.path.exists(resume_path):
        pytest.fail(f"Resume fixture not found at {resume_path}")

    # file:/// URI
    # On Windows: file:///C:/Path/To/File
    abs_html_path = os.path.abspath(html_path).replace("\", "/")
    url = f"file:///{abs_html_path}"
    
    candidate = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "555-1234",
        "resume_path": resume_path,
        "linkedin_url": "http://linkedin.com/in/test",
        "website_url": "http://example.com"
    }

    applier = GreenhouseApplier(headless=True)
    
    # Run application
    result = await applier.apply(url, candidate, submit=False)

    assert result["status"] == "dry_run"
    assert "Form filled" in result["message"]

if __name__ == "__main__":
    asyncio.run(test_apply_dry_run())
