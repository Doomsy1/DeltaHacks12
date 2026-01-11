"""
API Tests for the Headless Service.

Tests the deployed service at the specified BASE_URL.
Run with: py test_api.py

These tests verify:
1. Health endpoint
2. Authentication
3. Application listing
4. Application lifecycle (analyze -> submit/cancel)
5. 2FA verification flow
6. Error handling

See FRONTEND_INTEGRATION_GUIDE.md for API documentation.
"""
import asyncio
import httpx
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://155.138.132.178:8001"
USER_ID = "thomasariogpt@gmail.com"

# Known job ID from demo data
TEST_JOB_ID = "4092512009"


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def record(self, name: str, passed: bool, error: str = ""):
        if passed:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            self.errors.append((name, error))
            print(f"  [FAIL] {name}: {error}")

    def skip(self, name: str, reason: str = ""):
        self.skipped += 1
        print(f"  [SKIP] {name}: {reason}")

    def summary(self):
        print(f"\n{'=' * 60}")
        print(f"RESULTS: {self.passed} passed, {self.failed} failed, {self.skipped} skipped")
        if self.errors:
            print("\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print("=" * 60)


# =============================================================================
# Test: Health Check
# =============================================================================

async def test_health(client: httpx.AsyncClient, results: TestResults):
    """Test the health endpoint."""
    try:
        resp = await client.get(f"{BASE_URL}/health")
        results.record(
            "Health endpoint returns 200",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
        data = resp.json()
        results.record(
            "Health response has status field",
            data.get("status") == "ok",
            f"Got {data}"
        )
    except Exception as e:
        results.record("Health endpoint accessible", False, str(e))


# =============================================================================
# Test: Authentication
# =============================================================================

async def test_auth_required(client: httpx.AsyncClient, results: TestResults):
    """Test that X-User-ID header is required."""
    try:
        # No X-User-ID header
        resp = await client.get(f"{BASE_URL}/api/v1/applications")
        results.record(
            "List apps requires auth (401 without header)",
            resp.status_code == 401,
            f"Got {resp.status_code}"
        )

        # Test analyze endpoint
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/analyze",
            json={"job_id": TEST_JOB_ID, "auto_submit": False}
        )
        results.record(
            "Analyze requires auth (401 without header)",
            resp.status_code == 401,
            f"Got {resp.status_code}"
        )
    except Exception as e:
        results.record("Auth check works", False, str(e))


# =============================================================================
# Test: List Applications
# =============================================================================

async def test_list_applications(client: httpx.AsyncClient, results: TestResults):
    """Test listing applications."""
    headers = {"X-User-ID": USER_ID}
    try:
        resp = await client.get(f"{BASE_URL}/api/v1/applications", headers=headers)
        results.record(
            "List applications returns 200",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
        data = resp.json()
        results.record(
            "List response has applications array",
            "applications" in data and isinstance(data["applications"], list),
            f"Got {data.keys()}"
        )
        results.record(
            "List response has total count",
            "total" in data,
            f"Missing 'total' field"
        )

        # Test with status filter
        resp = await client.get(
            f"{BASE_URL}/api/v1/applications?status=submitted",
            headers=headers
        )
        results.record(
            "List with status filter returns 200",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )

        # Test pagination
        resp = await client.get(
            f"{BASE_URL}/api/v1/applications?limit=5&offset=0",
            headers=headers
        )
        results.record(
            "List with pagination returns 200",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
    except Exception as e:
        results.record("List applications works", False, str(e))


# =============================================================================
# Test: Error Handling
# =============================================================================

async def test_invalid_job_id(client: httpx.AsyncClient, results: TestResults):
    """Test analyze with invalid job ID."""
    headers = {"X-User-ID": USER_ID}
    payload = {"job_id": "invalid_id_12345", "auto_submit": False}
    try:
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/analyze",
            json=payload,
            headers=headers
        )
        results.record(
            "Invalid job ID returns 404",
            resp.status_code == 404,
            f"Got {resp.status_code}: {resp.text[:100]}"
        )
    except Exception as e:
        results.record("Invalid job ID handled", False, str(e))


async def test_application_not_found(client: httpx.AsyncClient, results: TestResults):
    """Test getting non-existent application."""
    headers = {"X-User-ID": USER_ID}
    fake_id = "000000000000000000000000"  # Valid ObjectId format but doesn't exist

    try:
        # GET non-existent
        resp = await client.get(
            f"{BASE_URL}/api/v1/applications/{fake_id}",
            headers=headers
        )
        results.record(
            "Non-existent application GET returns 404",
            resp.status_code == 404,
            f"Got {resp.status_code}"
        )

        # DELETE non-existent
        resp = await client.delete(
            f"{BASE_URL}/api/v1/applications/{fake_id}",
            headers=headers
        )
        results.record(
            "Non-existent application DELETE returns 404",
            resp.status_code == 404,
            f"Got {resp.status_code}"
        )

        # SUBMIT non-existent
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/{fake_id}/submit",
            json={"field_overrides": {}},
            headers=headers
        )
        results.record(
            "Non-existent application SUBMIT returns 404",
            resp.status_code == 404,
            f"Got {resp.status_code}"
        )

        # VERIFY non-existent
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/{fake_id}/verify",
            json={"code": "12345678"},
            headers=headers
        )
        results.record(
            "Non-existent application VERIFY returns 404",
            resp.status_code == 404,
            f"Got {resp.status_code}"
        )
    except Exception as e:
        results.record("Application not found handled", False, str(e))


# =============================================================================
# Test: Analyze Endpoint
# =============================================================================

async def test_analyze_endpoint(client: httpx.AsyncClient, results: TestResults) -> str | None:
    """Test the analyze endpoint. Returns application_id if successful."""
    headers = {"X-User-ID": USER_ID}

    # First, cancel any existing application for this job
    try:
        list_resp = await client.get(f"{BASE_URL}/api/v1/applications", headers=headers)
        apps = list_resp.json().get("applications", [])
        for app in apps:
            if str(app.get("job_id")) == TEST_JOB_ID and app.get("status") in ["analyzing", "pending_review", "pending_verification"]:
                await client.delete(
                    f"{BASE_URL}/api/v1/applications/{app['application_id']}",
                    headers=headers
                )
                print(f"    (Cancelled existing application {app['application_id']})")
    except:
        pass  # Ignore cleanup errors

    payload = {"job_id": TEST_JOB_ID, "auto_submit": False}
    try:
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/analyze",
            json=payload,
            headers=headers,
            timeout=120.0  # Analysis can take time
        )
        results.record(
            "Analyze returns 201",
            resp.status_code == 201,
            f"Got {resp.status_code}: {resp.text[:200]}"
        )

        if resp.status_code == 201:
            data = resp.json()
            results.record(
                "Analyze returns application_id",
                "application_id" in data,
                f"Missing application_id"
            )
            results.record(
                "Analyze returns fields",
                "fields" in data and len(data["fields"]) > 0,
                f"Got {len(data.get('fields', []))} fields"
            )
            results.record(
                "Analyze returns status pending_review",
                data.get("status") == "pending_review",
                f"Got status: {data.get('status')}"
            )
            results.record(
                "Analyze returns expires_at",
                "expires_at" in data,
                f"Missing expires_at"
            )
            results.record(
                "Analyze returns ttl_seconds",
                data.get("ttl_seconds") == 1800,
                f"Got ttl_seconds: {data.get('ttl_seconds')}"
            )
            results.record(
                "Analyze returns job info",
                "job" in data and all(k in data["job"] for k in ["id", "title", "company_name", "url"]),
                f"Missing job info fields"
            )
            results.record(
                "Analyze returns form_fingerprint",
                "form_fingerprint" in data,
                f"Missing form_fingerprint"
            )

            # Validate field structure
            if data.get("fields"):
                field = data["fields"][0]
                required_field_keys = ["field_id", "label", "field_type", "required", "source", "confidence", "editable"]
                results.record(
                    "Field has required keys",
                    all(k in field for k in required_field_keys),
                    f"Missing keys in field: {field.keys()}"
                )

            return data.get("application_id")
    except httpx.ReadTimeout:
        results.record("Analyze completes in time", False, "Timeout after 120s")
    except Exception as e:
        results.record("Analyze endpoint works", False, str(e))

    return None


async def test_duplicate_application(client: httpx.AsyncClient, results: TestResults, app_id: str):
    """Test that duplicate applications are rejected."""
    headers = {"X-User-ID": USER_ID}
    payload = {"job_id": TEST_JOB_ID, "auto_submit": False}

    try:
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/analyze",
            json=payload,
            headers=headers,
            timeout=30.0
        )
        results.record(
            "Duplicate application returns 409",
            resp.status_code == 409,
            f"Got {resp.status_code}: {resp.text[:100]}"
        )
    except Exception as e:
        results.record("Duplicate application handled", False, str(e))


# =============================================================================
# Test: Get Application
# =============================================================================

async def test_get_application(client: httpx.AsyncClient, results: TestResults, app_id: str):
    """Test getting an application by ID."""
    headers = {"X-User-ID": USER_ID}
    try:
        resp = await client.get(
            f"{BASE_URL}/api/v1/applications/{app_id}",
            headers=headers
        )
        results.record(
            "Get application returns 200",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
        data = resp.json()
        required_fields = ["application_id", "status", "job_id", "job_title", "company_name",
                          "user_id", "created_at", "updated_at"]
        results.record(
            "Application has required fields",
            all(k in data for k in required_fields),
            f"Missing fields: {set(required_fields) - set(data.keys())}"
        )
        results.record(
            "Application has fields array",
            "fields" in data and isinstance(data.get("fields"), list),
            f"Missing or invalid fields array"
        )
    except Exception as e:
        results.record("Get application works", False, str(e))


# =============================================================================
# Test: Verify Endpoint (State Checks)
# =============================================================================

async def test_verify_wrong_state(client: httpx.AsyncClient, results: TestResults, app_id: str):
    """Test that verify fails when application is not in pending_verification state."""
    headers = {"X-User-ID": USER_ID}

    try:
        # Application is in pending_review state, not pending_verification
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/{app_id}/verify",
            json={"code": "12345678"},
            headers=headers
        )
        results.record(
            "Verify in wrong state returns 409",
            resp.status_code == 409,
            f"Got {resp.status_code}: {resp.text[:100]}"
        )
    except Exception as e:
        results.record("Verify state check works", False, str(e))


# =============================================================================
# Test: Authorization
# =============================================================================

async def test_authorization(client: httpx.AsyncClient, results: TestResults, app_id: str):
    """Test that users can only access their own applications."""
    wrong_headers = {"X-User-ID": "wrong_user@example.com"}

    try:
        # Try to get another user's application
        resp = await client.get(
            f"{BASE_URL}/api/v1/applications/{app_id}",
            headers=wrong_headers
        )
        results.record(
            "Get other user's app returns 403",
            resp.status_code == 403,
            f"Got {resp.status_code}"
        )

        # Try to submit another user's application
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/{app_id}/submit",
            json={"field_overrides": {}},
            headers=wrong_headers
        )
        results.record(
            "Submit other user's app returns 403",
            resp.status_code == 403,
            f"Got {resp.status_code}"
        )

        # Try to verify another user's application
        resp = await client.post(
            f"{BASE_URL}/api/v1/applications/{app_id}/verify",
            json={"code": "12345678"},
            headers=wrong_headers
        )
        results.record(
            "Verify other user's app returns 403",
            resp.status_code == 403,
            f"Got {resp.status_code}"
        )

        # Try to cancel another user's application
        resp = await client.delete(
            f"{BASE_URL}/api/v1/applications/{app_id}",
            headers=wrong_headers
        )
        results.record(
            "Cancel other user's app returns 403",
            resp.status_code == 403,
            f"Got {resp.status_code}"
        )
    except Exception as e:
        results.record("Authorization check works", False, str(e))


# =============================================================================
# Test: Cancel Application
# =============================================================================

async def test_cancel_application(client: httpx.AsyncClient, results: TestResults, app_id: str):
    """Test cancelling an application."""
    headers = {"X-User-ID": USER_ID}
    try:
        resp = await client.delete(
            f"{BASE_URL}/api/v1/applications/{app_id}",
            headers=headers
        )
        results.record(
            "Cancel returns 200",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
        data = resp.json()
        results.record(
            "Cancel returns cancelled status",
            data.get("status") == "cancelled",
            f"Got status: {data.get('status')}"
        )
        results.record(
            "Cancel returns application_id",
            data.get("application_id") == app_id,
            f"Wrong application_id: {data.get('application_id')}"
        )

        # Try to cancel again - should still work
        resp = await client.delete(
            f"{BASE_URL}/api/v1/applications/{app_id}",
            headers=headers
        )
        results.record(
            "Cancel idempotent (already cancelled)",
            resp.status_code == 200,
            f"Got {resp.status_code}"
        )
    except Exception as e:
        results.record("Cancel application works", False, str(e))


# =============================================================================
# Test: Submit State Checks
# =============================================================================

async def test_submit_wrong_state(client: httpx.AsyncClient, results: TestResults):
    """Test that submit fails for submitted/expired applications."""
    headers = {"X-User-ID": USER_ID}

    # Find a submitted application if one exists
    try:
        list_resp = await client.get(
            f"{BASE_URL}/api/v1/applications?status=submitted&limit=1",
            headers=headers
        )
        apps = list_resp.json().get("applications", [])

        if apps:
            submitted_app_id = apps[0]["application_id"]
            resp = await client.post(
                f"{BASE_URL}/api/v1/applications/{submitted_app_id}/submit",
                json={"field_overrides": {}},
                headers=headers
            )
            # Should return 200 with "already_submitted" status
            data = resp.json() if resp.status_code == 200 else {}
            results.record(
                "Submit on submitted app returns already_submitted",
                resp.status_code == 200 and data.get("status") == "already_submitted",
                f"Got {resp.status_code}: {data.get('status', 'N/A')}"
            )
        else:
            results.skip("Submit on submitted app", "No submitted applications found")
    except Exception as e:
        results.record("Submit state check works", False, str(e))


# =============================================================================
# Main Test Runner
# =============================================================================

async def main():
    print("=" * 60)
    print("HEADLESS SERVICE API TESTS")
    print(f"Target: {BASE_URL}")
    print(f"User: {USER_ID}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    results = TestResults()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Basic connectivity
        print("\n[1] Health Check")
        await test_health(client, results)

        # Auth tests
        print("\n[2] Authentication Required")
        await test_auth_required(client, results)

        # List applications
        print("\n[3] List Applications")
        await test_list_applications(client, results)

        # Error handling
        print("\n[4] Error Handling - Invalid Inputs")
        await test_invalid_job_id(client, results)
        await test_application_not_found(client, results)

        # Application lifecycle
        print("\n[5] Application Lifecycle - Analyze")
        app_id = await test_analyze_endpoint(client, results)

        if app_id:
            print("\n[6] Duplicate Application Check")
            await test_duplicate_application(client, results, app_id)

            print("\n[7] Get Application")
            await test_get_application(client, results, app_id)

            print("\n[8] Verify Wrong State (before cancel)")
            await test_verify_wrong_state(client, results, app_id)

            print("\n[9] Authorization Checks")
            await test_authorization(client, results, app_id)

            print("\n[10] Cancel Application")
            await test_cancel_application(client, results, app_id)
        else:
            print("\n[6-10] Skipped (no application created)")

        # Submit state checks
        print("\n[11] Submit State Checks")
        await test_submit_wrong_state(client, results)

    results.summary()

    # Exit with error code if tests failed
    sys.exit(1 if results.failed > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
