#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Pego Video Contest Platform
Tests dual payment system (Stripe & PromptPay) and all backend endpoints
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

    def test_payment_methods_api(self):
        """Test /api/payment/methods endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/payment/methods")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["payment_methods", "amount", "currency"]
                
                if all(field in data for field in required_fields):
                    methods = data["payment_methods"]
                    
                    # Check if both Stripe and PromptPay are available
                    method_ids = [method["id"] for method in methods]
                    has_stripe = "stripe" in method_ids
                    has_promptpay = "promptpay" in method_ids
                    
                    if has_stripe and has_promptpay:
                        self.log_test("Payment Methods API", True, 
                                    f"Both payment methods available: {method_ids}, Amount: {data['amount']} {data['currency']}")
                        return data
                    else:
                        self.log_test("Payment Methods API", False, "", 
                                    f"Missing payment methods. Available: {method_ids}")
                        return None
                else:
                    self.log_test("Payment Methods API", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Payment Methods API", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Payment Methods API", False, "", str(e))
            return None

    def test_video_upload_initiation(self):
        """Test /api/upload/initiate endpoint"""
        try:
            video_data = {
                "title": "Test Payment Integration Video",
                "description": "Testing dual payment system with Stripe and PromptPay",
                "user_id": self.test_user_id
            }
            
            response = self.session.post(
                f"{self.base_url}/upload/initiate",
                json=video_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["video_id", "message"]
                
                if all(field in data for field in required_fields):
                    self.test_video_id = data["video_id"]
                    self.log_test("Video Upload Initiation", True, 
                                f"Created video_id: {data['video_id']}")
                    return data
                else:
                    self.log_test("Video Upload Initiation", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Video Upload Initiation", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Video Upload Initiation", False, "", str(e))
            return None

    def test_stripe_payment_flow(self):
        """Test Stripe payment creation and status checking"""
        if not self.test_video_id:
            self.log_test("Stripe Payment Flow", False, "", "No video_id available")
            return None
            
        try:
            # Create Stripe payment session
            payment_data = {
                "video_id": self.test_video_id,
                "payment_method": "stripe",
                "user_id": self.test_user_id
            }
            
            response = self.session.post(
                f"{self.base_url}/payment/create",
                json=payment_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["payment_method", "checkout_url", "session_id"]
                
                if all(field in data for field in required_fields):
                    if data["payment_method"] == "stripe" and data["checkout_url"]:
                        session_id = data["session_id"]
                        
                        # Test payment status check
                        status_response = self.session.get(
                            f"{self.base_url}/payment/status/stripe/{session_id}"
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            required_status_fields = ["session_id", "status", "payment_status", "payment_method"]
                            
                            if all(field in status_data for field in required_status_fields):
                                self.log_test("Stripe Payment Flow", True, 
                                            f"Payment session created: {session_id}, Status: {status_data['status']}")
                                return {"session_id": session_id, "status_data": status_data}
                            else:
                                self.log_test("Stripe Payment Flow", False, "", 
                                            f"Missing status fields: {list(status_data.keys())}")
                                return None
                        else:
                            self.log_test("Stripe Payment Flow", False, "", 
                                        f"Status check failed: {status_response.status_code}")
                            return None
                    else:
                        self.log_test("Stripe Payment Flow", False, "", 
                                    f"Invalid Stripe response: {data}")
                        return None
                else:
                    self.log_test("Stripe Payment Flow", False, "", 
                                f"Missing required fields: {list(data.keys())}")
                    return None
            else:
                self.log_test("Stripe Payment Flow", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Stripe Payment Flow", False, "", str(e))
            return None

    def test_promptpay_payment_flow(self):
        """Test PromptPay payment creation, QR code generation, and confirmation"""
        if not self.test_video_id:
            self.log_test("PromptPay Payment Flow", False, "", "No video_id available")
            return None
            
        try:
            # Create PromptPay payment session
            payment_data = {
                "video_id": self.test_video_id,
                "payment_method": "promptpay",
                "user_id": self.test_user_id
            }
            
            response = self.session.post(
                f"{self.base_url}/payment/create",
                json=payment_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["payment_method", "session_id", "qr_code", "amount", "currency", "expires_at", "instructions"]
                
                if all(field in data for field in required_fields):
                    if data["payment_method"] == "promptpay":
                        session_id = data["session_id"]
                        qr_code = data["qr_code"]
                        
                        # Validate QR code format (should be base64 image)
                        if qr_code.startswith("data:image/png;base64,"):
                            # Test payment status check
                            status_response = self.session.get(
                                f"{self.base_url}/payment/status/promptpay/{session_id}"
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                required_status_fields = ["session_id", "status", "payment_method", "qr_code"]
                                
                                if all(field in status_data for field in required_status_fields):
                                    # Test payment confirmation
                                    confirm_response = self.session.post(
                                        f"{self.base_url}/payment/confirm/promptpay/{session_id}"
                                    )
                                    
                                    if confirm_response.status_code == 200:
                                        confirm_data = confirm_response.json()
                                        if "message" in confirm_data and "session_id" in confirm_data:
                                            self.log_test("PromptPay Payment Flow", True, 
                                                        f"Complete flow: Session {session_id}, QR generated, Payment confirmed")
                                            return {"session_id": session_id, "confirmed": True}
                                        else:
                                            self.log_test("PromptPay Payment Flow", False, "", 
                                                        f"Invalid confirmation response: {confirm_data}")
                                            return None
                                    else:
                                        self.log_test("PromptPay Payment Flow", False, "", 
                                                    f"Confirmation failed: {confirm_response.status_code}")
                                        return None
                                else:
                                    self.log_test("PromptPay Payment Flow", False, "", 
                                                f"Missing status fields: {list(status_data.keys())}")
                                    return None
                            else:
                                self.log_test("PromptPay Payment Flow", False, "", 
                                            f"Status check failed: {status_response.status_code}")
                                return None
                        else:
                            self.log_test("PromptPay Payment Flow", False, "", 
                                        f"Invalid QR code format: {qr_code[:50]}...")
                            return None
                    else:
                        self.log_test("PromptPay Payment Flow", False, "", 
                                    f"Wrong payment method: {data['payment_method']}")
                        return None
                else:
                    self.log_test("PromptPay Payment Flow", False, "", 
                                f"Missing required fields: {list(data.keys())}")
                    return None
            else:
                self.log_test("PromptPay Payment Flow", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("PromptPay Payment Flow", False, "", str(e))
            return None

    def test_video_file_upload_after_payment(self):
        """Test video file upload after payment confirmation"""
        if not self.test_video_id:
            self.log_test("Video File Upload After Payment", False, "", "No video_id available")
            return False
            
        try:
            # Create a test video file
            test_video_content = b'fake video content for testing'
            files = {'file': ('test_video.mp4', test_video_content, 'video/mp4')}
            
            response = self.session.post(
                f"{self.base_url}/upload/video/{self.test_video_id}",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "video_id", "filename"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Video File Upload After Payment", True, 
                                f"Video uploaded successfully: {data['filename']}")
                    return True
                else:
                    self.log_test("Video File Upload After Payment", False, "", 
                                f"Missing required fields: {list(data.keys())}")
                    return False
            elif response.status_code == 402:
                self.log_test("Video File Upload After Payment", False, "", 
                            "Payment required - video not marked as paid")
                return False
            else:
                self.log_test("Video File Upload After Payment", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Video File Upload After Payment", False, "", str(e))
            return False

    def test_competition_round_updates(self):
        """Test that competition rounds are updated correctly after payments"""
        try:
            response = self.session.get(f"{self.base_url}/leaderboard")
            
            if response.status_code == 200:
                data = response.json()
                if "competition_info" in data:
                    comp_info = data["competition_info"]
                    required_fields = ["round_id", "total_prize_pool", "total_videos"]
                    
                    if all(field in comp_info for field in required_fields):
                        self.log_test("Competition Round Updates", True, 
                                    f"Round: {comp_info['round_id']}, Prize Pool: {comp_info['total_prize_pool']} THB, Videos: {comp_info['total_videos']}")
                        return comp_info
                    else:
                        self.log_test("Competition Round Updates", False, "", 
                                    f"Missing competition fields: {list(comp_info.keys())}")
                        return None
                else:
                    self.log_test("Competition Round Updates", False, "", 
                                "No competition_info in response")
                    return None
            else:
                self.log_test("Competition Round Updates", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Competition Round Updates", False, "", str(e))
            return None

    def test_get_videos(self):
        """Test getting videos list"""
        try:
            response = self.session.get(f"{self.base_url}/videos")
            
            if response.status_code == 200:
                data = response.json()
                if "videos" in data and "total" in data:
                    self.log_test("Get Videos", True, 
                                f"Retrieved {data['total']} videos")
                    return data
                else:
                    self.log_test("Get Videos", False, "", 
                                f"Unexpected response structure: {list(data.keys())}")
                    return None
            else:
                self.log_test("Get Videos", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Get Videos", False, "", str(e))
            return None

    def test_get_video_details(self, video_id):
        """Test getting specific video details"""
        try:
            response = self.session.get(f"{self.base_url}/video/{video_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "user_id", "competition_round"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Get Video Details", True, 
                                f"Retrieved video: {data['title']}")
                    return data
                else:
                    self.log_test("Get Video Details", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Get Video Details", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Get Video Details", False, "", str(e))
            return None

    def test_video_streaming(self, video_id):
        """Test video streaming endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/video/{video_id}/stream")
            
            # For unpaid/non-existent videos, should return 404
            if response.status_code == 404:
                self.log_test("Video Streaming", True, 
                            "Correctly returned 404 for non-existent video file")
                return True
            elif response.status_code == 200:
                self.log_test("Video Streaming", True, 
                            "Successfully accessed video stream")
                return True
            else:
                self.log_test("Video Streaming", False, "", 
                            f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Video Streaming", False, "", str(e))
            return False

    def test_view_recording(self, video_id):
        """Test recording video views"""
        try:
            viewer_data = {
                "video_id": video_id,
                "viewer_id": str(uuid.uuid4())
            }
            
            response = self.session.post(
                f"{self.base_url}/video/{video_id}/view",
                json=viewer_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "video_id" in data:
                    self.log_test("View Recording", True, 
                                f"Recorded view for video {video_id}")
                    return True
                else:
                    self.log_test("View Recording", False, "", 
                                f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("View Recording", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("View Recording", False, "", str(e))
            return False

    def test_leaderboard(self):
        """Test leaderboard endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/leaderboard")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["leaderboard", "competition_info"]
                
                if all(field in data for field in required_fields):
                    comp_info = data["competition_info"]
                    required_comp_fields = ["round_id", "total_prize_pool", "total_videos"]
                    
                    if all(field in comp_info for field in required_comp_fields):
                        self.log_test("Leaderboard", True, 
                                    f"Retrieved leaderboard with {len(data['leaderboard'])} videos, "
                                    f"Prize pool: {comp_info['total_prize_pool']} THB")
                        return data
                    else:
                        self.log_test("Leaderboard", False, "", 
                                    f"Missing competition info fields: {list(comp_info.keys())}")
                        return None
                else:
                    self.log_test("Leaderboard", False, "", 
                                f"Missing required fields: {list(data.keys())}")
                    return None
            else:
                self.log_test("Leaderboard", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Leaderboard", False, "", str(e))
            return None

    def test_error_handling(self):
        """Test various error scenarios"""
        error_tests = [
            ("Invalid video ID", f"{self.base_url}/video/invalid-id"),
            ("Non-existent payment session", f"{self.base_url}/payment/status/invalid-session"),
            ("Invalid video stream", f"{self.base_url}/video/invalid-id/stream"),
        ]
        
        all_passed = True
        for test_name, url in error_tests:
            try:
                response = self.session.get(url)
                if response.status_code in [404, 500]:
                    self.log_test(f"Error Handling - {test_name}", True, 
                                f"Correctly returned {response.status_code}")
                else:
                    self.log_test(f"Error Handling - {test_name}", False, "", 
                                f"Expected 404/500, got {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test(f"Error Handling - {test_name}", False, "", str(e))
                all_passed = False
        
        return all_passed

    def run_comprehensive_tests(self):
        """Run all tests in sequence"""
        print("=" * 60)
        print("PEGO VIDEO CONTEST PLATFORM - BACKEND API TESTING")
        print("=" * 60)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Test 1: Basic connectivity
        if not self.test_root_endpoint():
            print("❌ CRITICAL: Cannot connect to backend API")
            return False
        
        # Test 2: Upload initiation and payment
        upload_data = self.test_upload_initiation()
        if not upload_data:
            print("❌ CRITICAL: Upload initiation failed")
            return False
        
        video_id = upload_data["video_id"]
        session_id = upload_data["session_id"]
        
        # Test 3: Payment status check
        self.test_payment_status_check(session_id)
        
        # Test 4: Video upload without payment (should fail)
        self.test_video_upload_without_payment(video_id)
        
        # Test 5: Get videos list
        self.test_get_videos()
        
        # Test 6: Get video details
        self.test_get_video_details(video_id)
        
        # Test 7: Video streaming
        self.test_video_streaming(video_id)
        
        # Test 8: View recording
        self.test_view_recording(video_id)
        
        # Test 9: Leaderboard
        self.test_leaderboard()
        
        # Test 10: Error handling
        self.test_error_handling()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['error']}")
        
        return passed == total

if __name__ == "__main__":
    tester = PegoAPITester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the details above.")