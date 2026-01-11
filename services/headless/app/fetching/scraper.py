"""
Main scraper orchestration logic.

Orchestrates the full pipeline:
1. Load companies from companies.json
2. Fetch jobs from Greenhouse API
3. Generate Gemini embeddings
4. Store in MongoDB Atlas
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.db import ensure_indexes, get_job_count, upsert_job, mark_missing_jobs_as_expired
from app.rate_limiter import embedding_rate_limiter
from .embeddings import configure_gemini, create_job_embedding_text, generate_embedding
from .greenhouse import fetch_all_job_details, fetch_jobs_for_company


def load_companies() -> list[dict[str, Any]]:
    """Load companies from the data/companies.json file."""
    # Get the path relative to this file
    current_dir = Path(__file__).parent
    companies_path = current_dir.parent.parent / "data" / "companies.json"

    if not companies_path.exists():
        print(f"Companies file not found: {companies_path}")
        return []

    with open(companies_path, "r", encoding="utf-8") as f:
        return json.load(f)


def html_to_text(html: str | None) -> str:
    """Convert HTML to plain text using BeautifulSoup."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def extract_location(job: dict[str, Any]) -> str | None:
    """Extract location name from job details."""
    location = job.get("location")
    if isinstance(location, dict):
        return location.get("name")
    return location if isinstance(location, str) else None


def extract_department(job: dict[str, Any]) -> str | None:
    """Extract department name from job details."""
    departments = job.get("departments", [])
    if departments and isinstance(departments, list):
        first_dept = departments[0]
        if isinstance(first_dept, dict):
            return first_dept.get("name")
    return None


def transform_job_to_document(
    job: dict[str, Any],
    company_token: str,
    company_name: str,
) -> dict[str, Any]:
    """
    Transform a Greenhouse job response into our MongoDB document format.

    Args:
        job: Raw job details from Greenhouse API
        company_token: Company's Greenhouse board token
        company_name: Display name of the company

    Returns:
        Job document ready for MongoDB (without embedding)
    """
    description_html = job.get("content", "")
    description_text = html_to_text(description_html)

    # Parse updated_at timestamp
    updated_at_str = job.get("updated_at")
    updated_at = None
    if updated_at_str:
        try:
            # Greenhouse uses ISO format: "2024-01-15T10:30:00-05:00"
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            updated_at = datetime.utcnow()

    return {
        "greenhouse_id": job.get("id"),
        "company_token": company_token,
        "company_name": company_name,
        "title": job.get("title", ""),
        "location": extract_location(job),
        "department": extract_department(job),
        "description_html": description_html,
        "description_text": description_text,
        "absolute_url": job.get("absolute_url", ""),
        "updated_at": updated_at or datetime.utcnow(),
        "active": True,
    }


async def scrape_company(
    client: httpx.AsyncClient,
    company: dict[str, Any],
) -> int:
    """
    Scrape jobs for a single company.

    Args:
        client: httpx async client
        company: Company dict with 'token' and 'name' fields

    Returns:
        Number of jobs successfully scraped and stored
    """
    token = company.get("token", "")
    name = company.get("name", token)

    if not token:
        return 0

    print(f"[{name}] Starting scrape...")

    # Fetch job summaries
    print(f"[{name}] Fetching job list from API...")
    job_summaries = await fetch_jobs_for_company(client, token)
    if not job_summaries:
        print(f"[{name}] No jobs found")
        # Even if no jobs found, we should mark all existing jobs for this company as expired
        expired_count = await mark_missing_jobs_as_expired(token, [])
        if expired_count > 0:
            print(f"[{name}] Marked {expired_count} old jobs as expired")
        return 0

    print(f"[{name}] Found {len(job_summaries)} jobs, fetching full details...")

    # Fetch full details
    job_details = await fetch_all_job_details(client, token, job_summaries)
    print(f"[{name}] Retrieved {len(job_details)} job details")

    # Transform and store each job concurrently
    print(f"[{name}] Processing {len(job_details)} jobs concurrently...")
    
    async def process_job(idx: int, job: dict[str, Any]) -> bool:
        job_title = job.get("title", "Unknown")
        # print(f"[{name}] ({idx}/{len(job_details)}) Processing: {job_title}")
        
        # Transform to document format
        doc = transform_job_to_document(job, token, name)

        # Generate embedding
        # print(f"[{name}] ({idx}/{len(job_details)}) Generating embedding...")
        embedding_text = create_job_embedding_text(doc)
        
        # Rate limit for embeddings
        await embedding_rate_limiter.acquire()
        doc["embedding"] = await generate_embedding(embedding_text)

        # Store in MongoDB
        # print(f"[{name}] ({idx}/{len(job_details)}) Storing in database...")
        success = await upsert_job(doc)
        if success:
            print(f"[{name}] ({idx}/{len(job_details)}) ✓ Processed & Stored: {job_title}")
        else:
            print(f"[{name}] ({idx}/{len(job_details)}) ✗ Failed to store: {job_title}")
        return success

    # Create tasks for all jobs
    tasks = [
        process_job(idx, job) 
        for idx, job in enumerate(job_details, 1)
    ]
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    stored_count = sum(1 for r in results if r)
    print(f"[{name}] Complete! Stored {stored_count}/{len(job_details)} jobs")

    # Clean up expired jobs
    active_ids = [job.get("id") for job in job_details if job.get("id")]
    expired_count = await mark_missing_jobs_as_expired(token, active_ids)
    if expired_count > 0:
        print(f"[{name}] Clean up: Marked {expired_count} old jobs as expired")

    return stored_count


async def run_scraper() -> dict[str, Any]:
    """
    Run the full scraping pipeline.

    Returns:
        Summary dict with companies_scraped, jobs_stored, total_jobs
    """
    print("=" * 60)
    print("Starting Greenhouse Job Scraper")
    print("=" * 60)

    # Configure Gemini API
    print("Configuring Gemini API...")
    try:
        configure_gemini()
        print("✓ Gemini API configured successfully")
    except ValueError as e:
        print(f"✗ Failed to configure Gemini: {e}")
        return {"error": str(e)}

    # Ensure MongoDB indexes
    print("Ensuring MongoDB indexes...")
    try:
        await ensure_indexes()
        print("✓ MongoDB indexes ready")
    except Exception as e:
        print(f"✗ Failed to setup MongoDB: {e}")
        return {"error": str(e)}

    # Load companies
    print("Loading companies from JSON...")
    companies = load_companies()
    if not companies:
        print("✗ No companies to scrape")
        return {"error": "No companies found in companies.json"}

    print(f"✓ Loaded {len(companies)} companies")
    print()

    # Scrape all companies
    total_jobs = 0
    companies_scraped = 0

    async with httpx.AsyncClient() as client:
        for idx, company in enumerate(companies, 1):
            company_name = company.get('name', 'unknown')
            print(f"\n--- Company {idx}/{len(companies)}: {company_name} ---")
            try:
                jobs_stored = await scrape_company(client, company)
                total_jobs += jobs_stored
                if jobs_stored > 0:
                    companies_scraped += 1
            except Exception as e:
                print(f"✗ Error scraping {company_name}: {e}")
                import traceback
                traceback.print_exc()

            # Small delay between companies to be nice to the API
            print(f"Waiting 0.5s before next company...")
            await asyncio.sleep(0.5)

    # Get final count from database
    print("\nFetching final job count from database...")
    final_count = await get_job_count()

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE!")
    print("=" * 60)
    print(f"  Companies processed: {idx}/{len(companies)}")
    print(f"  Companies with jobs: {companies_scraped}")
    print(f"  Jobs stored this run: {total_jobs}")
    print(f"  Total jobs in database: {final_count}")
    print("=" * 60)

    return {
        "companies_scraped": companies_scraped,
        "companies_total": len(companies),
        "jobs_stored": total_jobs,
        "total_jobs_in_db": final_count,
    }


if __name__ == "__main__":
    # Allow running directly for testing
    asyncio.run(run_scraper())
