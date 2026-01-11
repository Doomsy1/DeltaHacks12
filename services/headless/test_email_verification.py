"""
Test script for email verification callback functionality.

This script simulates the email verification flow by:
1. Creating a mock GreenhouseApplier scenario
2. Testing the verification_callback mechanism
3. Allowing manual code entry via console

Usage:
    python test_email_verification.py
    python test_email_verification.py --code 12345678  # Pre-fill code for testing
"""

import asyncio
import argparse
from typing import Callable, Any


async def console_verification_callback(email: str | None = None) -> str:
    """
    Console-based verification callback that prompts user for code.
    
    Args:
        email: The email address where the verification code was sent
    
    Returns:
        str: The 8-digit verification code entered by the user
    """
    print("\n" + "=" * 60)
    print("EMAIL VERIFICATION REQUIRED")
    print("=" * 60)
    if email:
        print(f"A verification code has been sent to: {email}")
        print("Please check your email and enter the 8-digit code below.")
    else:
        print("A verification code has been sent to your email.")
        print("Please enter the 8-digit code below.")
    print("=" * 60)
    
    while True:
        try:
            prompt = f"\nEnter 8-digit code{' for ' + email if email else ''}: "
            code = await asyncio.get_event_loop().run_in_executor(
                None, 
                input, 
                prompt
            )
            code = code.strip()
            
            if len(code) == 8 and code.isdigit():
                print(f"✓ Code received: {code}")
                return code
            else:
                print(f"✗ Invalid code. Please enter exactly 8 digits (you entered {len(code)} characters)")
        except (EOFError, KeyboardInterrupt):
            print("\n✗ Verification cancelled")
            return ""


async def mock_verification_callback(email: str | None = None, prefilled_code: str | None = None) -> str:
    """
    Mock verification callback for testing.
    
    Args:
        email: The email address where the verification code was sent
        prefilled_code: Optional code to return immediately (for testing)
    
    Returns:
        str: The verification code
    """
    if prefilled_code:
        if email:
            print(f"✓ Using prefilled code for {email}: {prefilled_code}")
        else:
            print(f"✓ Using prefilled code: {prefilled_code}")
        return prefilled_code
    
    return await console_verification_callback(email)


async def test_verification_callback(callback: Callable[[], Any], email: str | None = None, test_code: str | None = None) -> dict[str, Any]:
    """
    Test the verification callback mechanism.
    
    Args:
        callback: The verification callback function to test
        email: The email address where the verification code was sent
        test_code: Optional test code to use
    
    Returns:
        dict: Test result with status and code
    """
    print("\n" + "=" * 60)
    print("TESTING EMAIL VERIFICATION CALLBACK")
    print("=" * 60)
    
    if email:
        print(f"\n📧 Email address: {email}")
    
    try:
        # Simulate email verification being triggered
        print("\n[Simulated] Email verification modal detected...")
        if email:
            print(f"[Simulated] Verification code sent to: {email}")
        print("[Simulated] Calling verification_callback...")
        
        # Call the callback
        if test_code:
            # For testing with a prefilled code
            if asyncio.iscoroutinefunction(callback):
                code = await callback()
            else:
                code = callback()
        else:
            code = await callback()
        
        # Validate the code
        if not code:
            return {
                "status": "error",
                "message": "No code provided (cancelled or empty)",
                "code": None,
                "email": email
            }
        
        if len(code) != 8:
            return {
                "status": "error",
                "message": f"Invalid code length: expected 8, got {len(code)}",
                "code": code,
                "email": email
            }
        
        if not code.isdigit():
            return {
                "status": "error",
                "message": "Code must contain only digits",
                "code": code,
                "email": email
            }
        
        return {
            "status": "success",
            "message": "Verification code received successfully",
            "code": code,
            "email": email
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Callback error: {str(e)}",
            "code": None,
            "email": email
        }


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test email verification callback functionality"
    )
    parser.add_argument(
        "--code",
        type=str,
        help="Pre-fill code for testing (8 digits)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Email address where verification code was sent"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock callback (doesn't prompt for input)"
    )
    args = parser.parse_args()
    
    # Validate test code if provided
    test_code = args.code
    if test_code:
        if len(test_code) != 8 or not test_code.isdigit():
            print("✗ Error: --code must be exactly 8 digits")
            return 1
        print(f"ℹ Test mode: Using code {test_code}")
    
    # Get email address
    email = args.email
    if not email:
        # Default test email if not provided
        email = "test@example.com"
        print(f"ℹ No email provided, using default: {email}")
    
    # Choose callback
    if args.mock and test_code:
        callback = lambda: mock_verification_callback(email, test_code)
    else:
        callback = lambda: console_verification_callback(email)
    
    # Run test
    result = await test_verification_callback(callback, email, test_code)
    
    # Print results
    print("\n" + "=" * 60)
    print("TEST RESULT")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    if result.get('email'):
        print(f"Email: {result['email']}")
    if result.get('code'):
        print(f"Code: {result['code']}")
    print("=" * 60)
    
    if result['status'] == 'success':
        print("\n✓ Verification callback test PASSED")
        print(f"\nYou can use this callback format in your application:")
        email_str = result.get('email', 'user@example.com')
        code_str = result['code']
        print(f"  async def verification_callback():")
        print(f"      print('Verification code sent to {email_str}')")
        print(f"      code = input('Enter 8-digit code: ')")
        print(f"      return code")
        print(f"\n  Or with prefilled code for testing:")
        print(f"  verification_callback = lambda: '{code_str}'")
    else:
        print("\n✗ Verification callback test FAILED")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
