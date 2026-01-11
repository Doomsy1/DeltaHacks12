# Email Verification Testing Guide

This guide explains how to test the email verification functionality.

## Frontend OTP Modal Testing

### From React Native Console/Debugger

When the app is running, you can trigger the OTP modal from the console:

```javascript
// In React Native Debugger, Chrome DevTools, or Metro console
__testTriggerOTP()
```

This will show the OTP input modal on screen where you can enter an 8-digit code.

**How to use:**
1. Start your React Native app
2. Open the console/debugger (Metro bundler console, Chrome DevTools, or React Native Debugger)
3. Type: `__testTriggerOTP()`
4. Press Enter
5. The OTP modal will appear on screen
6. Enter an 8-digit code and click "Verify"

## Backend/Service Testing

### Test Script Usage

Run the email verification callback test script:

```bash
cd services/headless

# Interactive mode (prompts for code with email address)
python3 test_email_verification.py --email user@example.com

# Test with a prefilled code
python3 test_email_verification.py --email user@example.com --code 12345678

# Mock mode (uses prefilled code without prompting)
python3 test_email_verification.py --email user@example.com --mock --code 12345678

# Without email (uses default test@example.com)
python3 test_email_verification.py --code 12345678
```

**Note:** The `--email` parameter shows which email address the verification code was sent to, making it easier to check the correct inbox during testing.

### Integration with GreenhouseApplier

To test email verification in an actual job application flow:

```python
from app.applying.greenhouse import GreenhouseApplier

async def test_verification():
    applier = GreenhouseApplier(headless=False)  # Set to False to see browser
    
    async def verification_callback():
        print("Email verification required!")
        code = input("Enter 8-digit code: ")
        return code.strip()
    
    result = await applier.fill_and_submit(
        url="https://jobs.example.com/apply/123",
        fields=[...],
        submit=True,
        verification_callback=verification_callback
    )
    
    print(f"Result: {result}")
```

### Manual Testing with manual_debug_greenhouse.py

The existing `manual_debug_greenhouse.py` script already includes email verification:

```bash
cd services/headless
python manual_debug_greenhouse.py --submit --visible
```

This will:
1. Launch a visible browser
2. Fill out the application form
3. If email verification is required, prompt for the code in the console
4. Continue with the submission

## Testing Checklist

- [ ] OTP modal appears when triggered from console
- [ ] Can enter 8-digit code in modal
- [ ] Code validation works (requires exactly 8 digits)
- [ ] Modal can be cancelled
- [ ] Verification callback works in backend script
- [ ] Code is passed correctly to application submission
