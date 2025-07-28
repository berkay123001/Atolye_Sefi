#!/usr/bin/env python3
"""
🎮 QUICK TEST DEMO - 5 Dakikada Test Case Ekleme
Öğrenci dostu test sistemi demo'su
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Senin test sisteminin minimal versiyonu
class SimpleTestDemo:
    """Basit test demo sistemi"""
    
    def __init__(self):
        self.test_results = []
    
    def run_simple_file_ops_test(self):
        """Basit file operations test - educational purpose"""
        
        print("🧪 SIMPLE FILE OPERATIONS TEST DEMO")
        print("=" * 50)
        
        # Test scenarios (senin sistemindeki gibi)
        test_cases = [
            {
                "input": "dosya oluştur test.txt",
                "expected": "file_created",
                "description": "Basit dosya oluşturma",
                "should_create_file": True
            },
            {
                "input": "klasör oluştur ./test_folder", 
                "expected": "folder_created",
                "description": "Klasör oluşturma testi",
                "should_create_folder": True
            },
            {
                "input": "dosya kopyala source.txt dest.txt",
                "expected": "file_copied", 
                "description": "Dosya kopyalama testi",
                "should_copy_file": True
            }
        ]
        
        print(f"📊 Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['description']}")
            print(f"   Input: '{test_case['input']}'")
            print(f"   Expected: {test_case['expected']}")
            
            # Simulated agent response (gerçek agent yok)
            simulated_response = self.simulate_agent_response(test_case["input"])
            
            # Test evaluation (senin sistemindeki gibi)
            success, details = self.evaluate_test_case(test_case, simulated_response)
            
            # Result
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   Response: '{simulated_response}'")
            print(f"   Result: {status}")
            
            if not success:
                print(f"   🚨 Issue: {details.get('issue', 'Unknown')}")
                self.create_simple_issue_report(test_case, simulated_response)
            
            # Store result
            self.test_results.append({
                "test_name": test_case["description"],
                "success": success,
                "details": details
            })
        
        # Summary
        self.print_test_summary()
    
    def simulate_agent_response(self, input_text: str) -> str:
        """Simulated agent responses for demo"""
        
        responses = {
            "dosya oluştur": "test.txt dosyası oluşturuldu",
            "klasör oluştur": "Klasör işlemleri henüz desteklenmiyor",  # Bu fail olacak
            "dosya kopyala": "Dosya başarıyla kopyalandı"
        }
        
        for keyword, response in responses.items():
            if keyword in input_text:
                return response
        
        return "Komut anlaşılamadı"
    
    def evaluate_test_case(self, test_case: dict, response: str) -> tuple:
        """Test case değerlendirmesi (senin sistemindeki mantık)"""
        
        details = {}
        success_criteria = []
        
        # Genel kriterler
        details["response_quality"] = len(response.strip()) > 10
        details["no_errors"] = "hata" not in response.lower() and "desteklenmiyor" not in response.lower()
        
        success_criteria.extend([details["response_quality"], details["no_errors"]])
        
        # Özel kriterler (test case'e göre)
        if test_case.get("should_create_file"):
            details["file_mentioned"] = "dosya" in response.lower() and "oluştur" in response.lower()
            success_criteria.append(details["file_mentioned"])
        
        if test_case.get("should_create_folder"):
            details["folder_operation"] = "klasör" in response.lower() and "oluştur" in response.lower()
            success_criteria.append(details["folder_operation"])
        
        if test_case.get("should_copy_file"):
            details["copy_mentioned"] = "kopyala" in response.lower()
            success_criteria.append(details["copy_mentioned"])
        
        # Overall success
        overall_success = all(success_criteria)
        
        if not overall_success:
            failed_criteria = [k for k, v in details.items() if not v]
            details["issue"] = f"Failed criteria: {', '.join(failed_criteria)}"
        
        return overall_success, details
    
    def create_simple_issue_report(self, test_case: dict, response: str):
        """Basit issue report (senin sistemindeki gibi ama minimal)"""
        
        issue = {
            "test_name": test_case["description"],
            "input": test_case["input"],
            "expected": test_case["expected"],
            "actual": response,
            "suggestions": [
                "Implement missing functionality",
                "Improve response quality",
                "Add error handling"
            ]
        }
        
        print(f"   📝 Issue Report Created: {issue}")
    
    def print_test_summary(self):
        """Test özeti"""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 TEST SUMMARY")
        print("=" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🚨 Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test_name']}")
    
    def demo_test_case_creation(self):
        """Test case oluşturma demo'su"""
        
        print("\n🎓 TEST CASE CREATION DEMO")
        print("=" * 40)
        
        print("📝 YENİ TEST CASE TEMPLATE:")
        
        template = '''
{
    "input": "kullanıcı komutu buraya",
    "expected": "beklenen_sonuç",
    "description": "Test açıklaması",
    "should_do_something": True  # Özel kriter
}
        '''
        
        print(template)
        
        print("\n🔧 EVALUATION LOGIC TEMPLATE:")
        
        eval_template = '''
# evaluate_test_case fonksiyonuna ekle:
if test_case.get("should_do_something"):
    details["something_done"] = "anahtar_kelime" in response.lower()
    success_criteria.append(details["something_done"])
        '''
        
        print(eval_template)
        
        print("\n✅ EKLEME ADAMLARI:")
        print("1. Test case'i kategoriye ekle")
        print("2. Evaluation logic'i ekle") 
        print("3. Test çalıştır")
        print("4. Sonuçları incele")

def main():
    """Demo çalıştır"""
    print("🎮 QUICK TEST DEMO - Educational Version")
    print("🎯 Purpose: Understanding test system mechanics")
    print("=" * 60)
    
    demo = SimpleTestDemo()
    
    # File operations test demo
    demo.run_simple_file_ops_test()
    
    # Test case creation demo
    demo.demo_test_case_creation()
    
    print(f"\n🎉 DEMO COMPLETE!")
    print(f"📚 Now you understand how the test system works!")
    print(f"🚀 Ready to add real test cases to advanced_test_categories.py")

if __name__ == "__main__":
    main()