# DeltaHacks12 Headless Service

## Project Overview

This directory (`services/headless`) contains the autonomous job automation service for the DeltaHacks12 platform. It is a Python-based microservice responsible for:
1.  **Fetching:** Scraping job listings from various boards (currently focused on Greenhouse).
2.  **Processing:** generating embeddings for job descriptions using Google Gemini.
3.  **Applying:** Autonomously filling out job application forms using Playwright and AI.

The service is built with **FastAPI** and uses **MongoDB** for persistence.

## **CRITICAL: Command Conventions (Windows)**

**Always use the following commands for this environment:**
-   **Python:** Use `py` (e.g., `py manual_debug_greenhouse.py`)
-   **Pip:** Use `uv pip` (e.g., `uv pip install -r requirements.txt`) or `uv` for other package management tasks.

## Architecture & Tech Stack

-   **Language:** Python 3.10+
-   **Framework:** FastAPI
-   **Browser Automation:** Playwright (Async API)
-   **Database:** MongoDB (via Motor async driver)
-   **AI/LLM:**
    -   **OpenRouter:** Used for intelligent form filling (determining answers based on user profile).
    -   **Google GenAI (Gemini):** Used for generating vector embeddings of job descriptions.
-   **Task Scheduling:** APScheduler (for periodic scraping).

## Directory Structure

*   `app/` - Main application source code.
    *   `main.py` - FastAPI entry point and lifecycle management (starts scraper).
    *   `ai.py` - AI integration. Handles calls to OpenRouter for form field reasoning.
    *   `db.py` - Database layer. Manages `users` and `jobs` collections.
    *   `applying/` - Modules for filling applications.
        *   `greenhouse.py` - Logic for navigating and filling Greenhouse.io forms.
    *   `fetching/` - Modules for finding jobs.
        *   `scraper.py` - Scrapes job boards.
        *   `embeddings.py` - Generates text embeddings.
*   `tests/` - Unit and integration tests.
    *   `fixtures/` - Test data (e.g., dummy resumes).
*   `manual_debug_greenhouse.py` - **Critical Debug Tool.** A standalone script that:
    1.  Upserts a test user to MongoDB.
    2.  Launches a visible browser instance.
    3.  Runs the AI-driven application process on a real URL.
    4.  Keeps the browser open for inspection.
*   `Dockerfile` - Production container definition (includes Playwright browsers).
*   `requirements.txt` - Python dependencies.

## Setup & Configuration

### Prerequisites
-   Python 3.10+
-   MongoDB Instance (Atlas or Local)
-   API Keys (OpenRouter, Google Gemini)

### Environment Variables
Create a `.env` file in this directory:

```env
# Database
MONGODB_URI=mongodb+srv://...
MONGODB_DB=app

# AI Configuration
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=google/gemini-2.0-flash-lite-preview-02-05:free

# Optional
ENV=development
```

### Installation

```bash
# 1. Install dependencies
uv pip install -r requirements.txt

# 2. Install Playwright browsers
py -m playwright install chromium
```

## Usage

### Running the Service (API)
The service runs as a web server that performs scraping in the background.

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Running the Debug Script (Manual Test)
To verify the application logic visually without running the full server:

```bash
py manual_debug_greenhouse.py
```
*This script will attempt to apply to a test job using a generated dummy user.*

## Key Workflows

### 1. Job Applying (`app/applying/greenhouse.py`)
-   **Standard Fields:** Fills known IDs (Name, Email, Phone) directly from the user profile.
-   **Dropdowns:**
    -   **Standard Selects:** Randomly picks a valid option.
    -   **Custom (React) Selects:** Simulates user interaction (Click -> ArrowDown -> Enter) to pick an option.
-   **Text Inputs:** Uses AI (`app.ai.get_field_value`) to generate answers based on the User Profile and Job Description.
-   **File Uploads:** Detects file inputs and uploads the user's resume/cover letter.

### 2. Job Fetching (`app/fetching/scraper.py`)
-   Periodically scrapes job boards.
-   Generates embeddings for new jobs.
-   Upserts jobs to MongoDB using `greenhouse_id` as the unique key.