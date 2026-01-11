"""
Greenhouse API client for fetching job listings and details.
"""

import asyncio
import os
from typing import Any

import httpx

from app.rate_limiter import job_rate_limiter

# Greenhouse API base URL
GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards"

# Default number of jobs to fetch per company
DEFAULT_JOBS_PER_COMPANY = 10


async def fetch_jobs_for_company(
    client: httpx.AsyncClient,
    company_token: str,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch job listings for a company from Greenhouse API.

    Args:
        client: httpx async client
        company_token: Company's Greenhouse board token (e.g., "reddit")
        limit: Maximum number of jobs to fetch (default from env or 10)

    Returns:
        List of job summary dictionaries
    """
    if limit is None:
        limit = int(os.getenv("JOBS_PER_COMPANY", DEFAULT_JOBS_PER_COMPANY))

    url = f"{GREENHOUSE_API_BASE}/{company_token}/jobs"

    try:
        await job_rate_limiter.acquire()
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        jobs = data.get("jobs", [])
        return jobs[:limit]
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching jobs for {company_token}: {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        print(f"Request error fetching jobs for {company_token}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching jobs for {company_token}: {e}")
        return []


async def fetch_job_details(
    client: httpx.AsyncClient,
    company_token: str,
    job_id: int,
) -> dict[str, Any] | None:
    """
    Fetch full job details from Greenhouse API.

    Args:
        client: httpx async client
        company_token: Company's Greenhouse board token
        job_id: Greenhouse job ID

    Returns:
        Job details dictionary or None on error
    """
    url = f"{GREENHOUSE_API_BASE}/{company_token}/jobs/{job_id}"

    try:
        # Note: rate limiter is applied in the caller (fetch_all_job_details) or here?
        # If fetch_job_details is called individually, it should be limited too.
        # But fetch_all_job_details calls it. I will apply it here to be safe, 
        # but wait, fetch_all_job_details uses semaphore. 
        # Better to apply it right before the request.
        
        # However, for this tool replacement, I should be careful not to duplicate limits.
        # But since fetch_all_job_details is the main batch fetcher, I will put it there 
        # as requested in the instruction.
        # actually, I will put it in fetch_with_semaphore as planned.
        
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching job {job_id} for {company_token}: {e.response.status_code}")
        return None
    except httpx.RequestError as e:
        print(f"Request error fetching job {job_id} for {company_token}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching job {job_id} for {company_token}: {e}")
        return None


async def fetch_all_job_details(
    client: httpx.AsyncClient,
    company_token: str,
    job_summaries: list[dict[str, Any]],
    concurrency: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch full details for multiple jobs with controlled concurrency.

    Args:
        client: httpx async client
        company_token: Company's Greenhouse board token
        job_summaries: List of job summary dicts (must have 'id' field)
        concurrency: Maximum concurrent requests

    Returns:
        List of job detail dictionaries (excluding failed fetches)
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def fetch_with_semaphore(job_id: int) -> dict[str, Any] | None:
        async with semaphore:
            await job_rate_limiter.acquire()
            return await fetch_job_details(client, company_token, job_id)

    tasks = [
        fetch_with_semaphore(job["id"])
        for job in job_summaries
        if "id" in job
    ]

    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
