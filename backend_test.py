#!/usr/bin/env python3
"""
Backend API Testing for French Text-to-Speech Application
Tests all TTS API endpoints with comprehensive error handling
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

class TTSAPITester:
    def __init__(self, base_url: str = "https://smart-tts.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {name}")
        if details:
            print(f"   Details: {details}")

    def test_health_check(self) -> bool:
        """Test health endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {response.status_code}, Service: {data.get('service', 'Unknown')}")
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}")
                
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_get_voices(self) -> Tuple[bool, List[Dict]]:
        """Test GET /api/tts/voices endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/tts/voices", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                voices = data.get('voices', [])
                expected_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
                
                voice_ids = [v.get('id') for v in voices]
                all_voices_present = all(voice_id in voice_ids for voice_id in expected_voices)
                
                if all_voices_present and len(voices) == 6:
                    self.log_test("Get Voices", True, f"Found {len(voices)} voices: {voice_ids}")
                    return True, voices
                else:
                    self.log_test("Get Voices", False, f"Expected 6 voices {expected_voices}, got {voice_ids}")
                    return False, voices
            else:
                self.log_test("Get Voices", False, f"Status: {response.status_code}")
                return False, []
                
        except Exception as e:
            self.log_test("Get Voices", False, f"Exception: {str(e)}")
            return False, []

    def test_generate_speech(self, text: str = "Bonjour! Ceci est un test de synthèse vocale avec ponctuation: points, virgules, et exclamations!", 
                           voice: str = "alloy", speed: float = 1.0) -> bool:
        """Test POST /api/tts/generate endpoint"""
        try:
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed
            }
            
            print(f"   Testing speech generation with voice '{voice}', speed {speed}x")
            response = self.session.post(f"{self.api_url}/tts/generate", json=payload, timeout=30)
            
            success = response.status_code == 200
            
            if success:
                # Check if response is audio content
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'audio' in content_type and content_length > 1000:  # Reasonable audio file size
                    self.log_test(f"Generate Speech ({voice}, {speed}x)", True, 
                                f"Audio generated: {content_length} bytes, type: {content_type}")
                    return True
                else:
                    self.log_test(f"Generate Speech ({voice}, {speed}x)", False, 
                                f"Invalid audio response: {content_length} bytes, type: {content_type}")
                    return False
            else:
                error_msg = f"Status: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    pass
                self.log_test(f"Generate Speech ({voice}, {speed}x)", False, error_msg)
                return False
                
        except Exception as e:
            self.log_test(f"Generate Speech ({voice}, {speed}x)", False, f"Exception: {str(e)}")
            return False

    def test_save_history(self, text: str = "Test historique", voice: str = "alloy", speed: float = 1.0) -> str:
        """Test POST /api/tts/history endpoint"""
        try:
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "duration": 2.5
            }
            
            response = self.session.post(f"{self.api_url}/tts/history", json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                history_id = data.get('id')
                if history_id:
                    self.log_test("Save History", True, f"History saved with ID: {history_id}")
                    return history_id
                else:
                    self.log_test("Save History", False, "No ID returned in response")
                    return ""
            else:
                self.log_test("Save History", False, f"Status: {response.status_code}")
                return ""
                
        except Exception as e:
            self.log_test("Save History", False, f"Exception: {str(e)}")
            return ""

    def test_get_history(self) -> Tuple[bool, List[Dict]]:
        """Test GET /api/tts/history endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/tts/history", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get History", True, f"Retrieved {len(data)} history items")
                    return True, data
                else:
                    self.log_test("Get History", False, "Response is not a list")
                    return False, []
            else:
                self.log_test("Get History", False, f"Status: {response.status_code}")
                return False, []
                
        except Exception as e:
            self.log_test("Get History", False, f"Exception: {str(e)}")
            return False, []

    def test_delete_history(self, history_id: str) -> bool:
        """Test DELETE /api/tts/history/{id} endpoint"""
        if not history_id:
            self.log_test("Delete History", False, "No history ID provided")
            return False
            
        try:
            response = self.session.delete(f"{self.api_url}/tts/history/{history_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                message = data.get('message', '')
                self.log_test("Delete History", True, f"Deleted successfully: {message}")
                return True
            else:
                self.log_test("Delete History", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Delete History", False, f"Exception: {str(e)}")
            return False

    def test_punctuation_understanding(self) -> bool:
        """Test AI understanding of French punctuation"""
        test_texts = [
            "Bonjour! Comment allez-vous? Très bien, merci.",
            "Attention: ceci est important! N'oubliez pas les détails.",
            "Les éléments suivants: pommes, poires, oranges... sont délicieux."
        ]
        
        all_passed = True
        for i, text in enumerate(test_texts):
            success = self.test_generate_speech(text, voice="nova", speed=1.0)
            if not success:
                all_passed = False
                
        return all_passed

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all backend API tests"""
        print("🚀 Starting comprehensive TTS API testing...")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Test 1: Health check
        health_ok = self.test_health_check()
        if not health_ok:
            print("❌ Health check failed - stopping tests")
            return self.get_test_summary()
        
        # Test 2: Get voices
        voices_ok, voices = self.test_get_voices()
        if not voices_ok:
            print("❌ Voice retrieval failed - continuing with limited tests")
        
        # Test 3: Generate speech with different voices and speeds
        if voices_ok:
            # Test with different voices
            for voice_info in voices[:3]:  # Test first 3 voices
                voice_id = voice_info.get('id', 'alloy')
                self.test_generate_speech(voice=voice_id, speed=1.0)
            
            # Test with different speeds
            for speed in [0.5, 1.5, 2.0]:
                self.test_generate_speech(voice="alloy", speed=speed)
        else:
            # Fallback test with default voice
            self.test_generate_speech()
        
        # Test 4: Punctuation understanding
        self.test_punctuation_understanding()
        
        # Test 5: History operations
        history_id = self.test_save_history()
        history_ok, history_items = self.test_get_history()
        
        if history_id:
            self.test_delete_history(history_id)
        
        return self.get_test_summary()

    def get_test_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        summary = {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": round(success_rate, 2),
            "test_results": self.test_results,
            "backend_url": self.base_url,
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_run - self.tests_passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test_name']}: {result['details']}")
        
        return summary

def main():
    """Main test execution"""
    tester = TTSAPITester()
    summary = tester.run_comprehensive_tests()
    
    # Save results to file
    results_file = f"/app/backend_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    return 0 if summary['success_rate'] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())