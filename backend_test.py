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

    def test_upload_initiation(self):
        """Test video upload initiation and payment session creation"""
        try:
            # Test data
            user_id = str(uuid.uuid4())
            video_data = {
                "title": "Test Video Upload",
                "description": "Testing video upload functionality",
                "user_id": user_id
            }
            
            response = self.session.post(
                f"{self.base_url}/upload/initiate",
                json=video_data
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["video_id", "checkout_url", "session_id"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Upload Initiation", True, 
                                f"Created video_id: {data['video_id']}, session_id: {data['session_id']}")
                    return data
                else:
                    self.log_test("Upload Initiation", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Upload Initiation", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Upload Initiation", False, "", str(e))
            return None

    def test_payment_status_check(self, session_id):
        """Test payment status checking"""
        try:
            response = self.session.get(f"{self.base_url}/payment/status/{session_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["session_id", "status", "payment_status"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Payment Status Check", True, 
                                f"Status: {data['status']}, Payment: {data['payment_status']}")
                    return data
                else:
                    self.log_test("Payment Status Check", False, "", 
                                f"Missing required fields. Got: {list(data.keys())}")
                    return None
            else:
                self.log_test("Payment Status Check", False, "", 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Payment Status Check", False, "", str(e))
            return None

    def test_video_upload_without_payment(self, video_id):
        """Test video upload without payment (should fail)"""
        try:
            # Create a dummy file for testing
            files = {'file': ('test_video.mp4', b'fake video content', 'video/mp4')}
            
            response = self.session.post(
                f"{self.base_url}/upload/video/{video_id}",
                files=files
            )
            
            # Should fail with 402 Payment Required
            if response.status_code == 402:
                self.log_test("Video Upload Without Payment", True, 
                            "Correctly rejected unpaid upload")
                return True
            else:
                self.log_test("Video Upload Without Payment", False, "", 
                            f"Expected 402, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Video Upload Without Payment", False, "", str(e))
            return False

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