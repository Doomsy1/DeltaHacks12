"""
Full Integration Test for the Headless Service.

Tests the complete application flow as documented in FRONTEND_INTEGRATION_GUIDE.md:

1. Health Check - Verify service is running
2. Cleanup - Cancel any existing pending applications
3. Analyze - Extract form fields and get AI recommendations
4. Get Application - Verify application state
5. Submit - Fill form and submit (may trigger 2FA)
6. Verify (if needed) - Complete email verification
7. Final Status - Confirm submission

This test demonstrates the full frontend integration flow including 2FA handling.

Target: http://155.138.132.178:8001
Run with: py test_full_flow.py
"""
import asyncio
import httpx
from datetime import datetime, timezone

# Configuration
BASE_URL = "http://localhost:8001"
USER_ID = "thomasariogpt@gmail.com"
TEST_JOB_ID = "4092512009"

# Timeouts (matching FRONTEND_INTEGRATION_GUIDE.md)
ANALYZE_TIMEOUT = 120.0   # 2 minutes for form analysis
SUBMIT_TIMEOUT = 600.0    # 10 minutes for browser automation
VERIFY_TIMEOUT = 60.0     # 1 minute for code verification


def print_section(num: int, title: str):
    """Print a section header."""
    print(f"\n[{num}] {title}")
    print("-" * 50)


def print_response_summary(data: dict, keys: list[str]):
    """Print selected keys from response."""
    for key in keys:
        if key in data:
            value = data[key]
            if isinstance(value, str) and len(value) > 60:
                value = value[:60] + "..."
            print(f"    {key}: {value}")


async def main():
    print("=" * 60)
    print("HEADLESS SERVICE - FULL INTEGRATION TEST")
    print("=" * 60)
    print(f"Target URL: {BASE_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Job ID: {TEST_JOB_ID}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    headers = {"X-User-ID": USER_ID, "Content-Type": "application/json"}
    app_id = None

    async with httpx.AsyncClient() as client:

        # =====================================================================
        # Step 1: Health Check
        # =====================================================================
        print_section(1, "Health Check")
        try:
            resp = await client.get(f"{BASE_URL}/health", timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                print(f"    Status: {data.get('status')}")
                print(f"    Service: {data.get('service', 'headless')}")
                print("    [PASS] Service is healthy")
            else:
                print(f"    [FAIL] Health check failed: {resp.status_code}")
                return
        except Exception as e:
            print(f"    [FAIL] Cannot connect to service: {e}")
            return

        # =====================================================================
        # Step 2: Cleanup - Cancel Existing Applications
        # =====================================================================
        print_section(2, "Cleanup Existing Applications")
        try:
            resp = await client.get(f"{BASE_URL}/api/v1/applications", headers=headers)
            apps = resp.json().get("applications", [])
            cancelled = 0

            for app in apps:
                if str(app.get("job_id")) == TEST_JOB_ID:
                    status = app.get("status")
                    # Cancel applications in cancellable states
                    if status in ["analyzing", "pending_review", "pending_verification", "submitting"]:
                        cancel_resp = await client.delete(
                            f"{BASE_URL}/api/v1/applications/{app['application_id']}",
                            headers=headers
                        )
                        if cancel_resp.status_code == 200:
                            cancelled += 1
                            print(f"    Cancelled: {app['application_id']} (was {status})")

            print(f"    [PASS] Cleaned up {cancelled} application(s)")
        except Exception as e:
            print(f"    [WARN] Cleanup error (continuing): {e}")

        # =====================================================================
        # Step 3: Analyze Application
        # =====================================================================
        print_section(3, "Analyze Application (POST /analyze)")
        print("    Extracting form fields and generating AI recommendations...")
        print(f"    (This may take up to {ANALYZE_TIMEOUT}s)")

        analyze_payload = {
            "job_id": TEST_JOB_ID,
            "auto_submit": False  # Two-phase flow: review first
        }

        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/applications/analyze",
                json=analyze_payload,
                headers=headers,
                timeout=ANALYZE_TIMEOUT
            )

            if resp.status_code == 201:
                data = resp.json()
                app_id = data.get("application_id")

                print(f"\n    [PASS] Analysis complete")
                print_response_summary(data, ["application_id", "status", "expires_at", "ttl_seconds", "form_fingerprint"])

                # Show job info
                if "job" in data:
                    print(f"\n    Job: {data['job'].get('title')} at {data['job'].get('company_name')}")

                # Show field summary
                fields = data.get("fields", [])
                print(f"\n    Fields extracted: {len(fields)}")

                # Show sample fields (first 5)
                if fields:
                    print("\n    Sample fields:")
                    for f in fields[:5]:
                        val = f.get("recommended_value", "")
                        val_preview = (val[:40] + "...") if val and len(val) > 40 else val or "(empty)"
                        confidence = f.get("confidence", 0)
                        source = f.get("source", "unknown")
                        print(f"      - {f.get('label')}: {val_preview}")
                        print(f"        [type={f.get('field_type')}, source={source}, confidence={confidence:.1f}]")

            elif resp.status_code == 409:
                print(f"    [WARN] Application already exists")
                print(f"    Response: {resp.text[:200]}")
                # Try to find existing application
                list_resp = await client.get(f"{BASE_URL}/api/v1/applications", headers=headers)
                apps = list_resp.json().get("applications", [])
                existing = next((a for a in apps if str(a.get("job_id")) == TEST_JOB_ID), None)
                if existing:
                    app_id = existing["application_id"]
                    print(f"    Using existing: {app_id} (status: {existing.get('status')})")
            else:
                print(f"    [FAIL] Analyze failed: {resp.status_code}")
                print(f"    Response: {resp.text[:200]}")
                return

        except httpx.ReadTimeout:
            print(f"    [FAIL] Analysis timed out after {ANALYZE_TIMEOUT}s")
            return
        except Exception as e:
            print(f"    [FAIL] Analysis error: {e}")
            return

        if not app_id:
            print("    [FAIL] No application ID obtained")
            return

        # =====================================================================
        # Step 4: Get Application Status
        # =====================================================================
        print_section(4, f"Get Application Status (GET /{app_id})")

        try:
            resp = await client.get(
                f"{BASE_URL}/api/v1/applications/{app_id}",
                headers=headers
            )

            if resp.status_code == 200:
                data = resp.json()
                print(f"    [PASS] Application retrieved")
                print_response_summary(data, ["application_id", "status", "job_title", "company_name", "created_at", "expires_at"])
            else:
                print(f"    [WARN] Could not get application: {resp.status_code}")

        except Exception as e:
            print(f"    [WARN] Get application error: {e}")

        # =====================================================================
        # Step 5: Submit Application
        # =====================================================================
        print_section(5, f"Submit Application (POST /{app_id}/submit)")
        print("    Launching headless browser to fill and submit form...")
        print(f"    (This may take up to {SUBMIT_TIMEOUT/60:.0f} minutes)")

        submit_payload = {
            "field_overrides": {},  # Use all recommended values
            "save_responses": True   # Cache for future applications
        }

        try:
            resp = await client.post(
                f"{BASE_URL}/api/v1/applications/{app_id}/submit",
                json=submit_payload,
                headers=headers,
                timeout=SUBMIT_TIMEOUT
            )

            if resp.status_code == 200:
                result = resp.json()
                status = result.get("status")

                print(f"\n    Status: {status}")
                print(f"    Message: {result.get('message')}")

                # ─────────────────────────────────────────────────────────────
                # Handle: pending_verification (2FA required)
                # ─────────────────────────────────────────────────────────────
                if status == "pending_verification":
                    print("\n" + "=" * 60)
                    print("EMAIL VERIFICATION REQUIRED (2FA)")
                    print("=" * 60)
                    print("Check your email for an 8-digit verification code.")
                    print("The browser session will expire in 15 minutes.")
                    print("=" * 60)

                    # Keep prompting until valid code or explicit skip
                    verification_complete = False
                    attempt = 0
                    max_attempts = 5

                    while not verification_complete and attempt < max_attempts:
                        attempt += 1
                        print(f"\n    Attempt {attempt}/{max_attempts}")
                        try:
                            code = input("    Enter 8-digit code (or 'skip' to skip): ").strip()
                        except EOFError:
                            print("\n    [INFO] Non-interactive mode detected - skipping verification")
                            print(f"    Run interactively to enter the code, or use:")
                            print(f"    curl -X POST {BASE_URL}/api/v1/applications/{app_id}/verify \\")
                            print(f"         -H 'X-User-ID: {USER_ID}' -H 'Content-Type: application/json' \\")
                            print(f"         -d '{{\"code\": \"YOUR_8_DIGIT_CODE\"}}'")
                            break

                        # Check for skip
                        if code.lower() == 'skip' or code == '':
                            print("\n    [SKIP] Verification skipped")
                            print("    Application remains in 'pending_verification' state")
                            print(f"    You can call POST /api/v1/applications/{app_id}/verify later")
                            break

                        # Validate code format
                        if len(code) != 8 or not code.isdigit():
                            print("    [ERROR] Code must be exactly 8 digits. Try again.")
                            continue

                        # Submit verification code
                        print_section(6, f"Verify Application (POST /{app_id}/verify)")
                        print(f"    Submitting verification code: {code}")

                        verify_payload = {"code": code}

                        try:
                            verify_resp = await client.post(
                                f"{BASE_URL}/api/v1/applications/{app_id}/verify",
                                json=verify_payload,
                                headers=headers,
                                timeout=VERIFY_TIMEOUT
                            )

                            verify_result = verify_resp.json()
                            verify_status = verify_result.get("status")

                            print(f"\n    Verify Status: {verify_status}")
                            print(f"    Message: {verify_result.get('message')}")

                            if verify_status == "submitted":
                                print(f"    Submitted At: {verify_result.get('submitted_at')}")
                                print("\n    [PASS] Application submitted after verification!")
                                verification_complete = True
                            elif verify_resp.status_code == 410:
                                print("\n    [EXPIRED] Browser session expired. Please re-submit.")
                                break
                            else:
                                print(f"    Error: {verify_result.get('error')}")
                                print("\n    [FAIL] Verification failed - try again with correct code")
                                # Continue loop to retry

                        except Exception as e:
                            print(f"\n    [ERROR] Verification request failed: {e}")
                            print("    Try again...")

                    if attempt >= max_attempts and not verification_complete:
                        print(f"\n    [FAIL] Max attempts ({max_attempts}) reached")

                # ─────────────────────────────────────────────────────────────
                # Handle: submitted (direct success)
                # ─────────────────────────────────────────────────────────────
                elif status == "submitted":
                    print(f"    Submitted At: {result.get('submitted_at')}")
                    print("\n    [PASS] Application submitted successfully!")

                # ─────────────────────────────────────────────────────────────
                # Handle: already_submitted
                # ─────────────────────────────────────────────────────────────
                elif status == "already_submitted":
                    print(f"    Submitted At: {result.get('submitted_at')}")
                    print("\n    [INFO] Application was already submitted")

                # ─────────────────────────────────────────────────────────────
                # Handle: failed
                # ─────────────────────────────────────────────────────────────
                elif status == "failed":
                    print(f"    Error: {result.get('error')}")
                    print("\n    [FAIL] Submission failed")

                else:
                    print(f"\n    [INFO] Unexpected status: {status}")

            elif resp.status_code == 409:
                print(f"    [FAIL] State conflict: {resp.text[:200]}")
            elif resp.status_code == 410:
                print(f"    [FAIL] Application expired: {resp.text[:200]}")
            elif resp.status_code == 422:
                print(f"    [FAIL] Form structure changed - re-analyze required")
            else:
                print(f"    [FAIL] Submit failed: {resp.status_code}")
                print(f"    Response: {resp.text[:200]}")

        except httpx.ReadTimeout:
            print(f"\n    [TIMEOUT] Request timed out after {SUBMIT_TIMEOUT}s")
            print("    This can happen if email verification is required.")
            print("    Check the application status to see if it's pending_verification.")
        except Exception as e:
            print(f"\n    [FAIL] Submit error: {e}")

        # =====================================================================
        # Step 7: Final Status Check
        # =====================================================================
        print_section(7, "Final Status Check")

        try:
            resp = await client.get(
                f"{BASE_URL}/api/v1/applications/{app_id}",
                headers=headers
            )

            if resp.status_code == 200:
                data = resp.json()
                final_status = data.get("status")

                print(f"    Final Status: {final_status}")

                if data.get("submitted_at"):
                    print(f"    Submitted At: {data.get('submitted_at')}")

                if data.get("error"):
                    print(f"    Error: {data.get('error')}")

                if data.get("expires_at"):
                    # Check if session is still valid
                    try:
                        expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
                        now = datetime.now(timezone.utc)
                        remaining = (expires - now).total_seconds()
                        if remaining > 0:
                            print(f"    Expires In: {int(remaining)}s")
                        else:
                            print(f"    Expired: Yes")
                    except:
                        print(f"    Expires At: {data.get('expires_at')}")

                # Summary
                if final_status == "submitted":
                    print("\n    [SUCCESS] Application flow completed successfully!")
                elif final_status == "pending_verification":
                    print("\n    [PENDING] Awaiting email verification")
                    print("    Call POST /api/v1/applications/{app_id}/verify with the 8-digit code")
                elif final_status == "pending_review":
                    print("\n    [PENDING] Application ready for review and submission")
                elif final_status == "failed":
                    print("\n    [FAILED] Application failed - see error above")
                else:
                    print(f"\n    [INFO] Application in '{final_status}' state")

        except Exception as e:
            print(f"    [FAIL] Could not get final status: {e}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("INTEGRATION TEST COMPLETE")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
