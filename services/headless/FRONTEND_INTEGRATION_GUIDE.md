# Frontend Integration Guide: Headless Job Application API

This guide explains how to integrate the headless service's job application API with a frontend client, including the two-phase application flow and email 2FA verification.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Application States](#application-states)
4. [API Endpoints](#api-endpoints)
5. [Complete Flow Examples](#complete-flow-examples)
6. [TypeScript Types](#typescript-types)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## Overview

The headless service provides a **two-phase job application flow**:

1. **Phase 1 (Analyze)**: Extract form fields and generate AI recommendations
2. **Phase 2 (Submit)**: Fill and submit the form with user-confirmed values

When Greenhouse requires email verification (2FA), a third step is needed:

3. **Phase 3 (Verify)**: Submit the 8-digit code from the verification email

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐
│   ANALYZE    │───▶│    SUBMIT    │───▶│  VERIFY (if needed)  │
│              │    │              │    │                      │
│ Extract form │    │ Fill & send  │    │ Enter 8-digit code   │
│ Get AI recs  │    │              │    │ from email           │
└──────────────┘    └──────────────┘    └──────────────────────┘
```

---

## Authentication

All API requests require the `X-User-ID` header:

```typescript
const headers = {
  'Content-Type': 'application/json',
  'X-User-ID': 'user@example.com'  // User's email/ID
};
```

> **Note**: In production, this should be replaced with JWT validation on the backend.

---

## Application States

Applications move through these states:

| State | Description | Next States |
|-------|-------------|-------------|
| `analyzing` | Form being extracted | `pending_review`, `submitting`, `failed` |
| `pending_review` | Waiting for user review (30-min TTL) | `submitting`, `expired`, `cancelled` |
| `submitting` | Browser filling form | `submitted`, `pending_verification`, `failed` |
| `pending_verification` | Waiting for email code (15-min TTL) | `submitted`, `failed` |
| `submitted` | **Success** - Application complete | - |
| `failed` | **Error** - See error field | - |
| `expired` | Review window expired | - |
| `cancelled` | User cancelled | - |

---

## API Endpoints

Base URL: `http://localhost:8001` (or your deployed URL)

### 1. Analyze Application

Extract form fields and get AI-generated recommendations.

```
POST /api/v1/applications/analyze
```

**Request:**
```typescript
{
  "job_id": "4092512009",      // Greenhouse job ID
  "auto_submit": false         // false = review mode, true = submit immediately
}
```

**Response (201 - Review Mode):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "status": "pending_review",
  "expires_at": "2026-01-11T12:30:00Z",
  "ttl_seconds": 1800,
  "job": {
    "id": "4092512009",
    "title": "Senior Software Engineer",
    "company_name": "Tech Corp",
    "url": "https://boards.greenhouse.io/company/jobs/4092512009"
  },
  "fields": [
    {
      "field_id": "first_name",
      "label": "First Name",
      "field_type": "text",
      "required": true,
      "options": null,
      "recommended_value": "John",
      "reasoning": "From user profile",
      "source": "profile",
      "confidence": 1.0,
      "editable": true
    },
    {
      "field_id": "resume",
      "label": "Resume",
      "field_type": "file",
      "required": true,
      "recommended_value": "/path/to/resume.pdf",
      "source": "profile",
      "confidence": 1.0,
      "editable": false   // File fields cannot be edited
    }
    // ... more fields
  ],
  "form_fingerprint": "a1b2c3d4e5f6..."
}
```

**Errors:**
- `401` - Missing X-User-ID header
- `404` - User or job not found
- `409` - Application already exists for this job
- `410` - Job posting removed
- `502` - Browser/AI analysis failed

---

### 2. Submit Application

Submit the analyzed application with optional field overrides.

```
POST /api/v1/applications/{application_id}/submit
```

**Request:**
```typescript
{
  "field_overrides": {
    "first_name": "Jonathan",     // Override recommended value
    "cover_letter": "Custom..."   // Only include changed fields
  },
  "save_responses": true          // Cache answers for future use
}
```

**Response (200 - Success):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "status": "submitted",
  "message": "Application submitted successfully",
  "submitted_at": "2026-01-11T12:15:30Z",
  "error": null
}
```

**Response (200 - Verification Required):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "status": "pending_verification",
  "message": "Email verification required. Check your email for the 8-digit code and call POST /{application_id}/verify",
  "submitted_at": null,
  "error": null
}
```

> **Important**: When `status === "pending_verification"`, the browser session is kept alive for **15 minutes**. The user must enter the verification code within this window.

**Errors:**
- `403` - Not authorized (wrong user)
- `404` - Application not found
- `409` - Application not in `pending_review` state
- `410` - Application expired
- `422` - Form structure changed (re-analyze required)
- `502` - Browser submission failed

---

### 3. Verify Application (2FA)

Submit the 8-digit verification code from email.

```
POST /api/v1/applications/{application_id}/verify
```

**Request:**
```typescript
{
  "code": "12345678"   // Exactly 8 digits
}
```

**Response (200 - Success):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "status": "submitted",
  "message": "Application submitted successfully",
  "submitted_at": "2026-01-11T12:20:00Z",
  "error": null
}
```

**Response (200 - Failed):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "status": "failed",
  "message": "Verification failed: Invalid code",
  "submitted_at": null,
  "error": "Verification failed: Invalid code"
}
```

**Errors:**
- `403` - Not authorized
- `404` - Application not found
- `409` - Application not in `pending_verification` state
- `410` - Verification session expired (15-min timeout)
- `502` - Code submission failed

---

### 4. Get Application Status

Check the current status of an application.

```
GET /api/v1/applications/{application_id}
```

**Response (200):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "user_id": "user@example.com",
  "job_id": "4092512009",
  "job_title": "Senior Software Engineer",
  "company_name": "Tech Corp",
  "status": "submitted",
  "fields": [...],               // Full field list
  "created_at": "2026-01-11T12:00:00Z",
  "updated_at": "2026-01-11T12:20:00Z",
  "submitted_at": "2026-01-11T12:20:00Z",
  "expires_at": null,
  "error": null
}
```

---

### 5. List Applications

Get all applications for the current user.

```
GET /api/v1/applications?status=pending_review&limit=20&offset=0
```

**Query Parameters:**
- `status` (optional) - Filter by status
- `limit` (default: 20, max: 100)
- `offset` (default: 0)

**Response (200):**
```typescript
{
  "applications": [
    {
      "application_id": "507f1f77bcf86cd799439011",
      "job_id": "4092512009",
      "job_title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "status": "submitted",
      "created_at": "2026-01-11T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 6. Cancel Application

Cancel a pending application.

```
DELETE /api/v1/applications/{application_id}
```

**Response (200):**
```typescript
{
  "application_id": "507f1f77bcf86cd799439011",
  "status": "cancelled"   // or "already_submitted"
}
```

---

## Complete Flow Examples

### Flow A: Submit Without Review (Auto-Submit)

Use when you want to skip the review step:

```typescript
const response = await fetch(`${BASE_URL}/api/v1/applications/analyze`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-User-ID': userId
  },
  body: JSON.stringify({
    job_id: jobId,
    auto_submit: true   // Skip review, submit immediately
  })
});

const result = await response.json();

if (result.status === 'submitted') {
  console.log('Application submitted!', result.submitted_at);
} else if (result.status === 'failed') {
  console.error('Submission failed:', result.error);
}
```

### Flow B: Two-Phase with Review

Standard flow with user review:

```typescript
// Step 1: Analyze
const analyzeRes = await fetch(`${BASE_URL}/api/v1/applications/analyze`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-User-ID': userId },
  body: JSON.stringify({ job_id: jobId, auto_submit: false })
});

const analyzeData = await analyzeRes.json();
const { application_id, fields, expires_at } = analyzeData;

// Display fields to user for review...
// User makes edits...

// Step 2: Submit with overrides
const submitRes = await fetch(`${BASE_URL}/api/v1/applications/${application_id}/submit`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-User-ID': userId },
  body: JSON.stringify({
    field_overrides: {
      'first_name': userEditedFirstName,
      'cover_letter': userEditedCoverLetter
    },
    save_responses: true
  })
});

const submitData = await submitRes.json();

if (submitData.status === 'submitted') {
  showSuccess('Application submitted!');
} else if (submitData.status === 'pending_verification') {
  showVerificationModal();  // User needs to enter email code
}
```

### Flow C: Complete 2FA Verification

When `pending_verification` status is returned:

```typescript
// After submit returns status: "pending_verification"
showVerificationModal();

// User enters the 8-digit code from their email
const code = await getUserInputCode();

// Step 3: Verify
const verifyRes = await fetch(`${BASE_URL}/api/v1/applications/${application_id}/verify`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-User-ID': userId },
  body: JSON.stringify({ code })
});

const verifyData = await verifyRes.json();

if (verifyData.status === 'submitted') {
  showSuccess('Application submitted successfully!');
} else {
  showError(`Verification failed: ${verifyData.message}`);
  // User can try again with correct code (within 15 min window)
}
```

### Flow D: Polling for Status Updates

If you need to check status asynchronously:

```typescript
async function pollUntilComplete(applicationId: string, maxWaitMs = 300000) {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitMs) {
    const res = await fetch(`${BASE_URL}/api/v1/applications/${applicationId}`, {
      headers: { 'X-User-ID': userId }
    });

    const data = await res.json();

    // Terminal states
    if (['submitted', 'failed', 'expired', 'cancelled'].includes(data.status)) {
      return data;
    }

    // Need user action
    if (data.status === 'pending_verification') {
      return data;  // Frontend should show code input
    }

    // Still processing
    await sleep(2000);
  }

  throw new Error('Timeout waiting for application completion');
}
```

---

## TypeScript Types

```typescript
// Enums
type ApplicationStatus =
  | 'analyzing'
  | 'pending_review'
  | 'submitting'
  | 'pending_verification'
  | 'submitted'
  | 'failed'
  | 'expired'
  | 'cancelled';

type FieldType = 'text' | 'textarea' | 'select' | 'react_select' | 'file' | 'checkbox' | 'radio';
type FieldSource = 'profile' | 'cached' | 'ai' | 'manual';

// Request Types
interface AnalyzeRequest {
  job_id: string;
  auto_submit?: boolean;  // default: false
}

interface SubmitRequest {
  field_overrides?: Record<string, string>;
  save_responses?: boolean;  // default: true
}

interface VerifyRequest {
  code: string;  // Exactly 8 digits
}

// Response Types
interface FormField {
  field_id: string;
  label: string;
  field_type: FieldType;
  required: boolean;
  options: string[] | null;
  recommended_value: string | null;
  reasoning: string | null;
  source: FieldSource;
  confidence: number;  // 0.0 - 1.0
  editable: boolean;
}

interface JobInfo {
  id: string;
  title: string;
  company_name: string;
  url: string;
}

interface AnalyzeResponse {
  application_id: string;
  status: 'pending_review';
  expires_at: string;  // ISO datetime
  ttl_seconds: number;
  job: JobInfo;
  fields: FormField[];
  form_fingerprint: string;
}

interface SubmitResponse {
  application_id: string;
  status: 'submitted' | 'pending_verification' | 'failed' | 'already_submitted';
  message: string;
  submitted_at: string | null;
  error: string | null;
}

interface VerifyResponse {
  application_id: string;
  status: 'submitted' | 'failed';
  message: string;
  submitted_at: string | null;
  error: string | null;
  expires_in_seconds: number | null;
}

interface ApplicationStatus {
  application_id: string;
  user_id: string;
  job_id: string;
  job_title: string;
  company_name: string;
  status: ApplicationStatus;
  fields: FormField[] | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  expires_at: string | null;
  error: string | null;
}

interface ApplicationListItem {
  application_id: string;
  job_id: string;
  job_title: string;
  company_name: string;
  status: string;
  created_at: string;
}

interface ApplicationListResponse {
  applications: ApplicationListItem[];
  total: number;
}

interface CancelResponse {
  application_id: string;
  status: 'cancelled' | 'already_submitted';
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 201 | Created (analyze) | Process response |
| 401 | Unauthorized | Check X-User-ID header |
| 403 | Forbidden | Wrong user - can't access this application |
| 404 | Not Found | Application/job doesn't exist |
| 409 | Conflict | Application exists or state mismatch |
| 410 | Gone | Application/session expired |
| 422 | Unprocessable | Form changed - re-analyze |
| 502 | Bad Gateway | Browser/AI service error |

### Example Error Handler

```typescript
async function handleApiCall<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));

    switch (response.status) {
      case 401:
        throw new Error('Please log in to continue');
      case 403:
        throw new Error('You do not have access to this application');
      case 404:
        throw new Error('Application or job not found');
      case 409:
        throw new Error(error.detail || 'Application conflict - please try again');
      case 410:
        throw new Error('Application expired - please start a new application');
      case 422:
        throw new Error('Form has changed - please re-analyze the application');
      case 502:
        throw new Error('Service temporarily unavailable - please try again');
      default:
        throw new Error(error.detail || 'An unexpected error occurred');
    }
  }

  return response.json();
}
```

---

## Best Practices

### 1. Handle Verification Timeout

The browser session expires after 15 minutes. Show a countdown to the user:

```typescript
// After receiving pending_verification status
const SESSION_TIMEOUT = 15 * 60 * 1000;  // 15 minutes
const startTime = Date.now();

const interval = setInterval(() => {
  const remaining = SESSION_TIMEOUT - (Date.now() - startTime);
  if (remaining <= 0) {
    clearInterval(interval);
    showExpiredMessage();
  } else {
    updateCountdown(Math.ceil(remaining / 1000));
  }
}, 1000);
```

### 2. Handle Review Expiration

The `pending_review` state expires after 30 minutes:

```typescript
// After receiving analyze response
const expiresAt = new Date(analyzeData.expires_at).getTime();
const now = Date.now();
const ttlMs = expiresAt - now;

if (ttlMs < 60000) {  // Less than 1 minute
  showWarning('Review window expiring soon!');
}
```

### 3. Retry Logic

Implement exponential backoff for transient errors:

```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(baseDelay * Math.pow(2, i));
    }
  }
  throw new Error('Max retries exceeded');
}
```

### 4. Show Field Confidence

Visual feedback based on confidence scores:

```typescript
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'green';   // High confidence
  if (confidence >= 0.7) return 'yellow';  // Medium - AI generated
  return 'red';                             // Low - needs review
}
```

### 5. Cancel Stale Applications

Before starting a new application, clean up existing ones:

```typescript
async function cleanupExistingApplications(jobId: string) {
  const list = await fetchApplications({ status: 'pending_review' });

  for (const app of list.applications) {
    if (app.job_id === jobId) {
      await cancelApplication(app.application_id);
    }
  }
}
```

---

## React Native / Expo Integration Example

For the ReelJobs frontend specifically:

```typescript
// services/headless.ts
const HEADLESS_URL = process.env.EXPO_PUBLIC_HEADLESS_URL || 'http://localhost:8001';

export async function applyToJob(
  userId: string,
  jobId: string,
  autoSubmit: boolean = true
): Promise<SubmitResponse> {
  const response = await fetch(`${HEADLESS_URL}/api/v1/applications/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId
    },
    body: JSON.stringify({
      job_id: jobId,
      auto_submit: autoSubmit
    })
  });

  return handleApiCall(response);
}

export async function submitVerificationCode(
  userId: string,
  applicationId: string,
  code: string
): Promise<VerifyResponse> {
  const response = await fetch(
    `${HEADLESS_URL}/api/v1/applications/${applicationId}/verify`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId
      },
      body: JSON.stringify({ code })
    }
  );

  return handleApiCall(response);
}
```

---

## Timeouts Reference

| Operation | Timeout | Notes |
|-----------|---------|-------|
| Analyze | 120s | Form extraction + AI |
| Submit | 600s (10 min) | Browser automation |
| Verify | 60s | Code submission |
| Review TTL | 30 min | pending_review expires |
| Session TTL | 15 min | Browser session for verification |

---

## Debugging

### Check Service Health

```bash
curl http://localhost:8001/health
# {"status":"ok","service":"headless","timestamp":"..."}
```

### List Your Applications

```bash
curl -H "X-User-ID: user@example.com" http://localhost:8001/api/v1/applications
```

### Check Specific Application

```bash
curl -H "X-User-ID: user@example.com" \
  http://localhost:8001/api/v1/applications/507f1f77bcf86cd799439011
```
