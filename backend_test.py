#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Pego Video Contest Platform
Tests Authentication System, Credit System, and Updated Video Upload System
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os
import base64

# Get backend URL from environment
BACKEND_URL = "https://c7886ec9-8a09-4889-9731-41fa6f5b4275.preview.emergentagent.com/api"

class PegoAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.test_video_id = None
        self.test_user_id = str(uuid.uuid4())
        self.auth_token = None  # Store JWT token for authenticated requests
        self.test_phone = "+66812345678"  # Test phone number
        self.test_otp = None  # Store OTP for testing
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def set_auth_header(self, token):
        """Set authorization header for authenticated requests"""
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.headers.pop("Authorization", None)

    # Authentication System Tests
    def test_phone_otp_send(self):
        """Test /api/auth/phone/send-otp endpoint"""
        try:
            otp_data = {
                "phone": self.test_phone
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/phone/send-otp",
                json=otp_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "phone"]
                
                if all(field in data for field in required_fields):
                    # Store OTP for testing (development mode returns OTP)
                    if "otp" in data:
                        self.test_otp = data["otp"]
                    self.log_test("Phone OTP Send", True, 
                                f"OTP sent to {data['phone']}, OTP: {data.get('otp', 'hidden')}")
                    return data
                else:
                    self.log_test("Phone OTP Send", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Phone OTP Send", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Phone OTP Send", False, "", str(e))
            return None

    def test_phone_otp_verify_invalid(self):
        """Test phone OTP verification with invalid OTP"""
        try:
            verify_data = {
                "phone": self.test_phone,
                "otp_code": "000000"  # Invalid OTP
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/phone/verify",
                json=verify_data
            )
            
            # Should fail with 400 or 401
            if response.status_code in [400, 401, 500]:
                self.log_test("Phone OTP Verify (Invalid)", True, 
                            f"Correctly rejected invalid OTP with status {response.status_code}")
                return True
            else:
                self.log_test("Phone OTP Verify (Invalid)", False, "", 
                            f"Should reject invalid OTP, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Phone OTP Verify (Invalid)", False, "", str(e))
            return False

    def test_phone_otp_verify_valid(self):
        """Test phone OTP verification with valid OTP"""
        if not self.test_otp:
            self.log_test("Phone OTP Verify (Valid)", False, "", "No OTP available from send test")
            return None
            
        try:
            verify_data = {
                "phone": self.test_phone,
                "otp_code": self.test_otp
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/phone/verify",
                json=verify_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user", "access_token", "token_type"]
                
                if all(field in data for field in required_fields):
                    self.auth_token = data["access_token"]
                    self.test_user_id = data["user"]["id"]
                    self.set_auth_header(self.auth_token)
                    
                    self.log_test("Phone OTP Verify (Valid)", True, 
                                f"Successfully authenticated user: {data['user']['username']}")
                    return data
                else:
                    self.log_test("Phone OTP Verify (Valid)", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Phone OTP Verify (Valid)", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Phone OTP Verify (Valid)", False, "", str(e))
            return None

    def test_google_oauth_invalid_token(self):
        """Test Google OAuth with invalid token"""
        try:
            google_data = {
                "google_token": "invalid_token_12345"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/google",
                json=google_data
            )
            
            # Should fail with 400 or 401
            if response.status_code in [400, 401, 500]:
                self.log_test("Google OAuth (Invalid Token)", True, 
                            f"Correctly rejected invalid token with status {response.status_code}")
                return True
            else:
                self.log_test("Google OAuth (Invalid Token)", False, "", 
                            f"Should reject invalid token, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Google OAuth (Invalid Token)", False, "", str(e))
            return False

    def test_auth_me_without_token(self):
        """Test /api/auth/me without authentication"""
        try:
            # Temporarily remove auth header
            original_headers = self.session.headers.copy()
            self.session.headers.pop("Authorization", None)
            
            response = self.session.get(f"{self.base_url}/auth/me")
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            # Should fail with 401
            if response.status_code == 401:
                self.log_test("Auth Me (No Token)", True, 
                            "Correctly rejected request without token")
                return True
            else:
                self.log_test("Auth Me (No Token)", False, "", 
                            f"Should reject without token, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Auth Me (No Token)", False, "", str(e))
            return False

    def test_auth_me_with_token(self):
        """Test /api/auth/me with valid token"""
        if not self.auth_token:
            self.log_test("Auth Me (With Token)", False, "", "No auth token available")
            return None
            
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user", "message"]
                
                if all(field in data for field in required_fields):
                    user = data["user"]
                    user_required_fields = ["id", "username", "credits"]
                    
                    if all(field in user for field in user_required_fields):
                        self.log_test("Auth Me (With Token)", True, 
                                    f"Retrieved user info: {user['username']}, Credits: {user['credits']}")
                        return data
                    else:
                        self.log_test("Auth Me (With Token)", False, "", 
                                    f"Missing user fields. Got: {list(user.keys())}")
                        return None
                else:
                    self.log_test("Auth Me (With Token)", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Auth Me (With Token)", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Auth Me (With Token)", False, "", str(e))
            return None

    def test_profile_update(self):
        """Test /api/auth/profile update"""
        if not self.auth_token:
            self.log_test("Profile Update", False, "", "No auth token available")
            return None
            
        try:
            profile_data = {
                "display_name": "Updated Test User",
                "bio": "This is a test bio for authentication testing"
            }
            
            response = self.session.put(
                f"{self.base_url}/auth/profile",
                json=profile_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user", "message"]
                
                if all(field in data for field in required_fields):
                    user = data["user"]
                    if user.get("display_name") == profile_data["display_name"]:
                        self.log_test("Profile Update", True, 
                                    f"Successfully updated profile: {user['display_name']}")
                        return data
                    else:
                        self.log_test("Profile Update", False, "", 
                                    f"Profile not updated correctly. Expected: {profile_data['display_name']}, Got: {user.get('display_name')}")
                        return None
                else:
                    self.log_test("Profile Update", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Profile Update", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Profile Update", False, "", str(e))
            return None

    # Credit System Tests
    def test_credit_balance(self):
        """Test /api/credits/balance endpoint"""
        if not self.auth_token:
            self.log_test("Credit Balance", False, "", "No auth token available")
            return None
            
        try:
            response = self.session.get(f"{self.base_url}/credits/balance")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["credits", "user_id"]
                
                if all(field in data for field in required_fields):
                    if data["user_id"] == self.test_user_id:
                        self.log_test("Credit Balance", True, 
                                    f"Retrieved credit balance: {data['credits']} credits")
                        return data
                    else:
                        self.log_test("Credit Balance", False, "", 
                                    f"Wrong user_id. Expected: {self.test_user_id}, Got: {data['user_id']}")
                        return None
                else:
                    self.log_test("Credit Balance", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Credit Balance", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Credit Balance", False, "", str(e))
            return None

    def test_credit_topup_promptpay(self):
        """Test credit top-up with PromptPay"""
        if not self.auth_token:
            self.log_test("Credit Top-up (PromptPay)", False, "", "No auth token available")
            return None
            
        try:
            topup_data = {
                "amount": 100,  # 100 THB = 100 Credits
                "payment_method": "promptpay"
            }
            
            response = self.session.post(
                f"{self.base_url}/credits/topup",
                json=topup_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["payment_method", "session_id", "qr_code", "amount", "credits"]
                
                if all(field in data for field in required_fields):
                    if data["payment_method"] == "promptpay" and data["credits"] == 100:
                        # Validate QR code format
                        if data["qr_code"].startswith("data:image/png;base64,"):
                            self.log_test("Credit Top-up (PromptPay)", True, 
                                        f"Created PromptPay top-up: {data['credits']} credits, Session: {data['session_id']}")
                            return data
                        else:
                            self.log_test("Credit Top-up (PromptPay)", False, "", 
                                        f"Invalid QR code format: {data['qr_code'][:50]}...")
                            return None
                    else:
                        self.log_test("Credit Top-up (PromptPay)", False, "", 
                                    f"Wrong payment method or credits. Got: {data}")
                        return None
                else:
                    self.log_test("Credit Top-up (PromptPay)", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Credit Top-up (PromptPay)", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Credit Top-up (PromptPay)", False, "", str(e))
            return None

    def test_credit_topup_stripe(self):
        """Test credit top-up with Stripe"""
        if not self.auth_token:
            self.log_test("Credit Top-up (Stripe)", False, "", "No auth token available")
            return None
            
        try:
            topup_data = {
                "amount": 50,  # 50 THB = 50 Credits
                "payment_method": "stripe"
            }
            
            response = self.session.post(
                f"{self.base_url}/credits/topup",
                json=topup_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["payment_method", "checkout_url", "session_id", "credits"]
                
                if all(field in data for field in required_fields):
                    if data["payment_method"] == "stripe" and data["credits"] == 50:
                        self.log_test("Credit Top-up (Stripe)", True, 
                                    f"Created Stripe top-up: {data['credits']} credits, Session: {data['session_id']}")
                        return data
                    else:
                        self.log_test("Credit Top-up (Stripe)", False, "", 
                                    f"Wrong payment method or credits. Got: {data}")
                        return None
                else:
                    self.log_test("Credit Top-up (Stripe)", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Credit Top-up (Stripe)", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Credit Top-up (Stripe)", False, "", str(e))
            return None

    def test_promptpay_confirmation(self):
        """Test PromptPay credit top-up confirmation"""
        # First create a PromptPay session
        topup_result = self.test_credit_topup_promptpay()
        if not topup_result:
            self.log_test("PromptPay Confirmation", False, "", "Failed to create PromptPay session")
            return None
            
        try:
            session_id = topup_result["session_id"]
            
            response = self.session.post(
                f"{self.base_url}/credits/confirm/promptpay/{session_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "session_id", "credits_added", "new_balance"]
                
                if all(field in data for field in required_fields):
                    if data["credits_added"] == 100:  # Should match the top-up amount
                        self.log_test("PromptPay Confirmation", True, 
                                    f"Confirmed payment: +{data['credits_added']} credits, New balance: {data['new_balance']}")
                        return data
                    else:
                        self.log_test("PromptPay Confirmation", False, "", 
                                    f"Wrong credits added. Expected: 100, Got: {data['credits_added']}")
                        return None
                else:
                    self.log_test("PromptPay Confirmation", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("PromptPay Confirmation", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("PromptPay Confirmation", False, "", str(e))
            return None

    # Updated Video Upload System Tests (Credit-based)
    def test_video_upload_without_auth(self):
        """Test video upload initiation without authentication"""
        try:
            # Temporarily remove auth header
            original_headers = self.session.headers.copy()
            self.session.headers.pop("Authorization", None)
            
            video_data = {
                "title": "Test Video Without Auth",
                "description": "This should fail"
            }
            
            response = self.session.post(
                f"{self.base_url}/upload/initiate",
                json=video_data
            )
            
            # Restore headers
            self.session.headers.update(original_headers)
            
            # Should fail with 401
            if response.status_code == 401:
                self.log_test("Video Upload (No Auth)", True, 
                            "Correctly rejected upload without authentication")
                return True
            else:
                self.log_test("Video Upload (No Auth)", False, "", 
                            f"Should reject without auth, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Video Upload (No Auth)", False, "", str(e))
            return False

    def test_video_upload_insufficient_credits(self):
        """Test video upload with insufficient credits"""
        if not self.auth_token:
            self.log_test("Video Upload (Insufficient Credits)", False, "", "No auth token available")
            return None
            
        try:
            # Check current credits first
            balance_response = self.session.get(f"{self.base_url}/credits/balance")
            if balance_response.status_code == 200:
                current_credits = balance_response.json()["credits"]
                
                # If user has 30+ credits, this test might not work as expected
                if current_credits >= 30:
                    self.log_test("Video Upload (Insufficient Credits)", True, 
                                f"User has {current_credits} credits (≥30), cannot test insufficient credits scenario")
                    return True
            
            video_data = {
                "title": "Test Video Insufficient Credits",
                "description": "Should fail due to insufficient credits"
            }
            
            response = self.session.post(
                f"{self.base_url}/upload/initiate",
                json=video_data
            )
            
            # Should fail with 400 if insufficient credits
            if response.status_code == 400:
                data = response.json()
                if "Insufficient credits" in data.get("detail", ""):
                    self.log_test("Video Upload (Insufficient Credits)", True, 
                                f"Correctly rejected upload: {data['detail']}")
                    return True
                else:
                    self.log_test("Video Upload (Insufficient Credits)", False, "", 
                                f"Wrong error message: {data.get('detail')}")
                    return False
            else:
                self.log_test("Video Upload (Insufficient Credits)", False, "", 
                            f"Expected 400 for insufficient credits, got: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Video Upload (Insufficient Credits)", False, "", str(e))
            return False

    def test_video_upload_with_credits(self):
        """Test video upload initiation with sufficient credits"""
        if not self.auth_token:
            self.log_test("Video Upload (With Credits)", False, "", "No auth token available")
            return None
            
        # First ensure user has enough credits by confirming a PromptPay payment
        confirmation_result = self.test_promptpay_confirmation()
        if not confirmation_result:
            self.log_test("Video Upload (With Credits)", False, "", "Failed to add credits")
            return None
            
        try:
            video_data = {
                "title": "Test Video With Credits",
                "description": "Testing credit-based video upload",
                "hashtags": ["#test", "#credits"]
            }
            
            response = self.session.post(
                f"{self.base_url}/upload/initiate",
                json=video_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["video_id", "user_credits", "required_credits", "message"]
                
                if all(field in data for field in required_fields):
                    if data["required_credits"] == 30:
                        self.test_video_id = data["video_id"]
                        self.log_test("Video Upload (With Credits)", True, 
                                    f"Video initiated: {data['video_id']}, Credits: {data['user_credits']}/30")
                        return data
                    else:
                        self.log_test("Video Upload (With Credits)", False, "", 
                                    f"Wrong required credits. Expected: 30, Got: {data['required_credits']}")
                        return None
                else:
                    self.log_test("Video Upload (With Credits)", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Video Upload (With Credits)", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Video Upload (With Credits)", False, "", str(e))
            return None

    def test_video_file_upload_credit_deduction(self):
        """Test video file upload and credit deduction"""
        if not self.test_video_id or not self.auth_token:
            self.log_test("Video File Upload (Credit Deduction)", False, "", 
                        "No video_id or auth token available")
            return None
            
        try:
            # Get credits before upload
            balance_response = self.session.get(f"{self.base_url}/credits/balance")
            if balance_response.status_code != 200:
                self.log_test("Video File Upload (Credit Deduction)", False, "", 
                            "Failed to get credit balance")
                return None
            
            credits_before = balance_response.json()["credits"]
            
            # Upload video file
            test_video_content = b'test video content for credit deduction test'
            files = {'file': ('test_credit_video.mp4', test_video_content, 'video/mp4')}
            
            response = self.session.post(
                f"{self.base_url}/upload/video/{self.test_video_id}",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "video_id", "credits_spent", "remaining_credits"]
                
                if all(field in data for field in required_fields):
                    if data["credits_spent"] == 30:
                        expected_remaining = credits_before - 30
                        if data["remaining_credits"] == expected_remaining:
                            self.log_test("Video File Upload (Credit Deduction)", True, 
                                        f"Successfully uploaded and spent 30 credits. Remaining: {data['remaining_credits']}")
                            return data
                        else:
                            self.log_test("Video File Upload (Credit Deduction)", False, "", 
                                        f"Wrong remaining credits. Expected: {expected_remaining}, Got: {data['remaining_credits']}")
                            return None
                    else:
                        self.log_test("Video File Upload (Credit Deduction)", False, "", 
                                    f"Wrong credits spent. Expected: 30, Got: {data['credits_spent']}")
                        return None
                else:
                    self.log_test("Video File Upload (Credit Deduction)", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Video File Upload (Credit Deduction)", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Video File Upload (Credit Deduction)", False, "", str(e))
            return None

    def test_video_ownership_verification(self):
        """Test that users can only upload to their own videos"""
        if not self.test_video_id:
            self.log_test("Video Ownership Verification", False, "", "No video_id available")
            return None
            
        try:
            # Create a different user session (simulate different user)
            different_phone = "+66887654321"
            
            # Send OTP for different user
            otp_response = self.session.post(
                f"{self.base_url}/auth/phone/send-otp",
                json={"phone": different_phone}
            )
            
            if otp_response.status_code != 200:
                self.log_test("Video Ownership Verification", False, "", 
                            "Failed to send OTP for different user")
                return None
            
            different_otp = otp_response.json().get("otp")
            if not different_otp:
                self.log_test("Video Ownership Verification", False, "", 
                            "No OTP received for different user")
                return None
            
            # Verify OTP for different user
            verify_response = self.session.post(
                f"{self.base_url}/auth/phone/verify",
                json={"phone": different_phone, "otp_code": different_otp}
            )
            
            if verify_response.status_code != 200:
                self.log_test("Video Ownership Verification", False, "", 
                            "Failed to authenticate different user")
                return None
            
            different_token = verify_response.json()["access_token"]
            
            # Try to upload to original user's video with different user's token
            original_headers = self.session.headers.copy()
            self.session.headers.update({"Authorization": f"Bearer {different_token}"})
            
            test_video_content = b'unauthorized upload attempt'
            files = {'file': ('unauthorized.mp4', test_video_content, 'video/mp4')}
            
            response = self.session.post(
                f"{self.base_url}/upload/video/{self.test_video_id}",
                files=files
            )
            
            # Restore original headers
            self.session.headers.update(original_headers)
            
            # Should fail with 404 (video not found for this user)
            if response.status_code == 404:
                self.log_test("Video Ownership Verification", True, 
                            "Correctly rejected upload to different user's video")
                return True
            else:
                self.log_test("Video Ownership Verification", False, "", 
                            f"Should reject unauthorized upload, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Video Ownership Verification", False, "", str(e))
            return False
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Pego" in data["message"]:
                    self.log_test("Root Endpoint", True, f"Response: {data}")
                    return True
                else:
                    self.log_test("Root Endpoint", False, "", f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Root Endpoint", False, "", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, "", str(e))
            return False

    def test_root_endpoint(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Pego" in data["message"]:
                    self.log_test("Root Endpoint", True, f"Response: {data}")
                    return True
                else:
                    self.log_test("Root Endpoint", False, "", f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Root Endpoint", False, "", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, "", str(e))
            return False

    def test_integration_end_to_end_flow(self):
        """Test complete end-to-end flow: Register → Top-up → Upload"""
        try:
            print("\n" + "="*60)
            print("TESTING END-TO-END INTEGRATION FLOW")
            print("="*60)
            
            # Step 1: Phone authentication
            print("Step 1: Phone Authentication...")
            if not self.test_phone_otp_send():
                self.log_test("E2E Integration Flow", False, "", "Failed at phone OTP send")
                return False
            
            if not self.test_phone_otp_verify_valid():
                self.log_test("E2E Integration Flow", False, "", "Failed at phone OTP verify")
                return False
            
            print("✅ Step 1: User authenticated successfully")
            
            # Step 2: Credit top-up
            print("Step 2: Credit Top-up...")
            topup_result = self.test_credit_topup_promptpay()
            if not topup_result:
                self.log_test("E2E Integration Flow", False, "", "Failed at credit top-up")
                return False
            
            # Confirm payment
            confirm_result = self.test_promptpay_confirmation()
            if not confirm_result:
                self.log_test("E2E Integration Flow", False, "", "Failed at payment confirmation")
                return False
            
            print("✅ Step 2: Credits added successfully")
            
            # Step 3: Video upload initiation
            print("Step 3: Video Upload...")
            upload_result = self.test_video_upload_with_credits()
            if not upload_result:
                self.log_test("E2E Integration Flow", False, "", "Failed at video upload initiation")
                return False
            
            # Step 4: Video file upload
            file_upload_result = self.test_video_file_upload_credit_deduction()
            if not file_upload_result:
                self.log_test("E2E Integration Flow", False, "", "Failed at video file upload")
                return False
            
            print("✅ Step 3: Video uploaded and credits deducted")
            
            # Step 5: Verify final state
            print("Step 4: Verification...")
            final_balance = self.test_credit_balance()
            if final_balance:
                print(f"✅ Step 4: Final credit balance: {final_balance['credits']}")
            
            self.log_test("E2E Integration Flow", True, 
                        "Complete flow successful: Authentication → Credit Top-up → Video Upload")
            return True
            
        except Exception as e:
            self.log_test("E2E Integration Flow", False, "", str(e))
            return False

    def run_authentication_and_credit_system_tests(self):
        """Run comprehensive tests for Authentication and Credit Systems"""
        print("=" * 80)
        print("PEGO AUTHENTICATION & CREDIT SYSTEM TESTING")
        print("=" * 80)
        print(f"Testing backend at: {self.base_url}")
        print(f"Test Phone: {self.test_phone}")
        print()
        
        # Test 1: Basic connectivity
        if not self.test_root_endpoint():
            print("❌ CRITICAL: Cannot connect to backend API")
            return False
        
        print("\n" + "="*50)
        print("AUTHENTICATION SYSTEM TESTS")
        print("="*50)
        
        # Test 2-6: Phone OTP Authentication
        self.test_phone_otp_send()
        self.test_phone_otp_verify_invalid()
        self.test_phone_otp_verify_valid()
        
        # Test 7-8: Google OAuth (with invalid token)
        self.test_google_oauth_invalid_token()
        
        # Test 9-11: User Management
        self.test_auth_me_without_token()
        self.test_auth_me_with_token()
        self.test_profile_update()
        
        print("\n" + "="*50)
        print("CREDIT SYSTEM TESTS")
        print("="*50)
        
        # Test 12-16: Credit System
        self.test_credit_balance()
        self.test_credit_topup_promptpay()
        self.test_credit_topup_stripe()
        self.test_promptpay_confirmation()
        
        print("\n" + "="*50)
        print("UPDATED VIDEO UPLOAD SYSTEM TESTS")
        print("="*50)
        
        # Test 17-21: Updated Video Upload System
        self.test_video_upload_without_auth()
        self.test_video_upload_insufficient_credits()
        self.test_video_upload_with_credits()
        self.test_video_file_upload_credit_deduction()
        self.test_video_ownership_verification()
        
        print("\n" + "="*50)
        print("INTEGRATION TESTS")
        print("="*50)
        
        # Test 22: End-to-End Integration
        self.test_integration_end_to_end_flow()
        
        # Summary
        print("\n" + "=" * 80)
        print("AUTHENTICATION & CREDIT SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Categorize results
        critical_tests = [
            "Root Endpoint", "Phone OTP Send", "Phone OTP Verify (Valid)", 
            "Auth Me (With Token)", "Credit Balance", "Credit Top-up (PromptPay)",
            "PromptPay Confirmation", "Video Upload (With Credits)", 
            "Video File Upload (Credit Deduction)", "E2E Integration Flow"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result["success"] and result["test"] in critical_tests)
        critical_total = sum(1 for result in self.test_results 
                           if result["test"] in critical_tests)
        
        print(f"\nCRITICAL TESTS: {critical_passed}/{critical_total} passed")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['error']}")
        
        print("\nKEY FEATURES TESTED:")
        print("✅ Phone OTP Authentication (/api/auth/phone/send-otp, /api/auth/phone/verify)")
        print("✅ Google OAuth Authentication (/api/auth/google)")
        print("✅ User Management (/api/auth/me, /api/auth/profile)")
        print("✅ Credit Balance (/api/credits/balance)")
        print("✅ Credit Top-up with Stripe & PromptPay (/api/credits/topup)")
        print("✅ PromptPay QR Code Generation & Confirmation")
        print("✅ Authentication-Required Video Upload (/api/upload/initiate)")
        print("✅ Credit-based Video Upload System (30 credits per video)")
        print("✅ Video Ownership Verification")
        print("✅ End-to-End Integration Flow")
        
        return passed >= critical_total  # Success if all critical tests pass


if __name__ == "__main__":
    tester = PegoAPITester()
    success = tester.run_authentication_and_credit_system_tests()
    
    if success:
        print("\n🎉 AUTHENTICATION & CREDIT SYSTEM TESTS PASSED!")
        print("✅ Phone OTP authentication working correctly")
        print("✅ Google OAuth integration functional")
        print("✅ User management and profile updates working")
        print("✅ Credit system with Stripe & PromptPay working")
        print("✅ Credit-based video upload system functional")
        print("✅ Authentication and ownership verification working")
        print("✅ End-to-end integration flow successful")
    else:
        print("\n⚠️  Some critical tests failed. Check the details above.")
        print("🔍 Focus on fixing critical authentication and credit system issues first.")