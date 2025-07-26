#!/usr/bin/env python3
"""
🧪 ADVANCED TEST CATEGORIES SYSTEM
Claude Code entegrasyonu ile gelişmiş test kategorileri ve otomatik hata düzeltme sistemi
"""

import json
import time
import os
import sys
import traceback
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
import google.generativeai as genai

# Import the terminal agent
try:
    from tools.terminal_agent import TerminalAgent, AdvancedIntentClassifier
    from tools.automated_test_suite import TestResult, TerminalAgentTestSuite
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from terminal_agent import TerminalAgent, AdvancedIntentClassifier
        from automated_test_suite import TestResult, TerminalAgentTestSuite
    except ImportError:
        print("❌ Error: Could not import required modules. Make sure all files are available.")
        sys.exit(1)

@dataclass
class IssueReport:
    """Detaylı issue raporu yapısı"""
    issue_id: str
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    test_input: str
    expected_behavior: str
    actual_behavior: str
    error_trace: Optional[str]
    suggested_fixes: List[str]
    claude_analysis: Optional[str]
    timestamp: str
    status: str  # OPEN, IN_PROGRESS, RESOLVED, CLOSED

@dataclass
class TestCategory:
    """Test kategorisi yapısı"""
    name: str
    description: str
    test_cases: List[Dict]
    priority: str
    gemini_enhanced: bool = False

class AdvancedTestCategoriesSystem:
    """Gelişmiş test kategorileri sistemi - Claude Code entegrasyonu ile"""
    
    def __init__(self):
        """Initialize advanced test system"""
        self.agent = TerminalAgent()
        self.base_test_suite = TerminalAgentTestSuite()
        self.test_results: List[TestResult] = []
        self.issue_reports: List[IssueReport] = []
        self.start_time = None
        self.end_time = None
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Gemini setup
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            print("⚠️ GEMINI_API_KEY not found. Gemini features will be disabled.")
            self.gemini_model = None
        
        # 🎯 GELİŞMİŞ TEST KATEGORİLERİ
        self.advanced_categories = {
            "claude_code_integration": TestCategory(
                name="Claude Code Integration Tests",
                description="Claude Code ile entegrasyon testleri",
                priority="CRITICAL",
                gemini_enhanced=True,
                test_cases=[
                    {
                        "input": "claude code ile dosya analizi yap",
                        "expected_claude_integration": True,
                        "should_suggest_claude_commands": True,
                        "description": "Claude Code dosya analizi entegrasyonu"
                    },
                    {
                        "input": "hataları claude ile düzelt",
                        "expected_claude_integration": True,
                        "should_provide_fix_commands": True,
                        "description": "Claude Code hata düzeltme entegrasyonu"
                    },
                    {
                        "input": "test sonuçlarını claude'a gönder",
                        "expected_export_format": "claude_compatible",
                        "should_create_analysis_prompts": True,
                        "description": "Claude Code test sonucu aktarımı"
                    }
                ]
            ),
            
            "gemini_enhanced_testing": TestCategory(
                name="Gemini Enhanced Testing",
                description="Gemini AI ile geliştirilmiş test senaryoları",
                priority="HIGH",
                gemini_enhanced=True,
                test_cases=[
                    {
                        "input": "gemini ile test senaryosu oluştur",
                        "expected_gemini_usage": True,
                        "test_scenario_quality": "professional",
                        "description": "Gemini test senaryosu oluşturma"
                    },
                    {
                        "input": "karmaşık python problemi çöz",
                        "expected_complexity_handling": "advanced",
                        "should_use_gemini_reasoning": True,
                        "description": "Gemini karmaşık problem çözme"
                    },
                    {
                        "input": "kod kalitesi analizi yap",
                        "expected_analysis_depth": "comprehensive",
                        "should_provide_recommendations": True,
                        "description": "Gemini kod kalitesi analizi"
                    }
                ]
            ),
            
            "error_recovery_system": TestCategory(
                name="Error Recovery System Tests",
                description="Hata kurtarma ve otomatik düzeltme testleri",
                priority="HIGH",
                gemini_enhanced=False,
                test_cases=[
                    {
                        "input": "bozuk kod dosyası düzelt",
                        "should_detect_syntax_errors": True,
                        "should_suggest_fixes": True,
                        "expected_recovery_success": True,
                        "description": "Syntax hatası kurtarma"
                    },
                    {
                        "input": "eksik import'ları bul ve ekle",
                        "should_detect_missing_imports": True,
                        "should_auto_add_imports": True,
                        "description": "Eksik import kurtarma"
                    },
                    {
                        "input": "runtime hatası çöz",
                        "should_analyze_runtime_error": True,
                        "should_provide_solution": True,
                        "description": "Runtime hata kurtarma"
                    }
                ]
            ),
            
            "performance_optimization": TestCategory(
                name="Performance Optimization Tests",
                description="Performans optimizasyonu testleri",
                priority="MEDIUM",
                gemini_enhanced=True,
                test_cases=[
                    {
                        "input": "kodu optimize et",
                        "expected_optimization_suggestions": True,
                        "should_measure_improvement": True,
                        "description": "Kod optimizasyonu"
                    },
                    {
                        "input": "bellek kullanımını azalt",
                        "should_analyze_memory_usage": True,
                        "should_suggest_memory_optimizations": True,
                        "description": "Bellek optimizasyonu"
                    },
                    {
                        "input": "hız iyileştirmesi yap",
                        "should_profile_performance": True,
                        "should_suggest_speed_improvements": True,
                        "description": "Hız optimizasyonu"
                    }
                ]
            ),
            
            "security_analysis": TestCategory(
                name="Security Analysis Tests",
                description="Güvenlik analizi testleri",
                priority="HIGH",
                gemini_enhanced=True,
                test_cases=[
                    {
                        "input": "güvenlik açığı tara",
                        "should_detect_vulnerabilities": True,
                        "should_suggest_security_fixes": True,
                        "description": "Güvenlik açığı tarama"
                    },
                    {
                        "input": "kod güvenliği analizi",
                        "expected_security_report": True,
                        "should_rate_security_level": True,
                        "description": "Kod güvenliği analizi"
                    },
                    {
                        "input": "güvenli kod yazmak için öneriler",
                        "should_provide_security_guidelines": True,
                        "should_give_best_practices": True,
                        "description": "Güvenlik önerileri"
                    }
                ]
            ),
            
            "ml_workflow_testing": TestCategory(
                name="ML Workflow Testing",
                description="Machine Learning iş akışı testleri",
                priority="MEDIUM",
                gemini_enhanced=True,
                test_cases=[
                    {
                        "input": "makine öğrenmesi modeli oluştur",
                        "should_create_ml_pipeline": True,
                        "expected_model_quality": "production_ready",
                        "description": "ML model oluşturma"
                    },
                    {
                        "input": "veri analizi raporu hazırla",
                        "should_analyze_data": True,
                        "should_create_visualizations": True,
                        "description": "Veri analizi raporu"
                    },
                    {
                        "input": "model performansını değerlendir",
                        "should_calculate_metrics": True,
                        "should_suggest_improvements": True,
                        "description": "Model performans değerlendirme"
                    }
                ]
            ),
            
            "collaborative_development": TestCategory(
                name="Collaborative Development Tests",
                description="İşbirlikli geliştirme testleri",
                priority="MEDIUM",
                gemini_enhanced=False,
                test_cases=[
                    {
                        "input": "kod review yap",
                        "should_analyze_code_quality": True,
                        "should_suggest_improvements": True,
                        "description": "Kod review"
                    },
                    {
                        "input": "git commit mesajı oluştur",
                        "should_generate_commit_message": True,
                        "expected_message_quality": "professional",
                        "description": "Git commit mesajı oluşturma"
                    },
                    {
                        "input": "dokümantasyon yaz",
                        "should_create_documentation": True,
                        "expected_documentation_completeness": "comprehensive",
                        "description": "Dokümantasyon oluşturma"
                    }
                ]
            )
        }
    
    def generate_gemini_test_scenarios(self, category: str, complexity_level: str = "advanced") -> List[Dict]:
        """Gemini ile gelişmiş test senaryoları oluştur"""
        if not self.gemini_model:
            print("⚠️ Gemini model not available. Skipping scenario generation.")
            return []
        
        prompt = f"""
        {category} kategorisi için {complexity_level} seviyesinde test senaryoları oluştur.
        
        Her test senaryosu şu format'ta olmalı:
        - input: Test girdisi (Türkçe)
        - expected_behavior: Beklenen davranış
        - complexity_score: 1-10 arası karmaşıklık skoru
        - success_criteria: Başarı kriterleri
        - edge_cases: Sınır durumları
        - description: Test açıklaması
        
        5 farklı test senaryosu oluştur. JSON formatında döndür.
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            # Gemini response'unu parse et
            gemini_scenarios = json.loads(response.text)
            return gemini_scenarios.get('scenarios', [])
        except Exception as e:
            print(f"⚠️ Gemini scenario generation failed: {str(e)}")
            return []
    
    def run_advanced_category_tests(self, category_name: str = None) -> str:
        """Gelişmiş kategori testlerini çalıştır"""
        self.start_time = datetime.now()
        print("🧪 ADVANCED TEST CATEGORIES SYSTEM")
        print("=" * 80)
        print(f"📅 Test Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Claude Code Integration + Gemini Enhanced Testing")
        print("=" * 80)
        
        categories_to_test = [category_name] if category_name else list(self.advanced_categories.keys())
        
        for cat_name in categories_to_test:
            if cat_name not in self.advanced_categories:
                print(f"❌ Unknown category: {cat_name}")
                continue
                
            category = self.advanced_categories[cat_name]
            print(f"\n🔍 Running {category.name} Tests...")
            print(f"📝 Description: {category.description}")
            print(f"⚡ Priority: {category.priority}")
            
            # Gemini ile geliştirilmiş senaryolar
            if category.gemini_enhanced:
                print("🤖 Generating Gemini-enhanced scenarios...")
                gemini_scenarios = self.generate_gemini_test_scenarios(cat_name)
                if gemini_scenarios:
                    category.test_cases.extend(gemini_scenarios)
                    print(f"✨ Added {len(gemini_scenarios)} Gemini-generated scenarios")
            
            # Test cases'leri çalıştır
            self.execute_category_tests(category, cat_name)
        
        self.end_time = datetime.now()
        
        # Raporları oluştur ve issue'ları kaydet
        self.generate_issue_reports()
        self.export_claude_integration_data()
        
        return self.create_claude_fix_commands()
    
    def execute_category_tests(self, category: TestCategory, category_name: str):
        """Kategori testlerini çalıştır"""
        print(f"\n📊 {category.name} - Executing {len(category.test_cases)} test cases")
        print("-" * 60)
        
        for i, test_case in enumerate(category.test_cases, 1):
            start_time = time.time()
            
            try:
                # Test case'i çalıştır
                response = self.agent.process_request(test_case["input"])
                response_time = time.time() - start_time
                
                # Test sonucunu değerlendir
                success, details = self.evaluate_test_case(test_case, response, category_name)
                
                # Test result oluştur
                test_result = TestResult(
                    test_type=category_name,
                    test_name=test_case.get("description", f"Test {i}"),
                    input_text=test_case["input"],
                    expected=str(test_case.get("expected_behavior", "Success")),
                    actual=response[:200] + "..." if len(response) > 200 else response,
                    success=success,
                    response_time=response_time,
                    details=details
                )
                self.test_results.append(test_result)
                
                # Issue raporu oluştur (başarısız testler için)
                if not success:
                    self.create_issue_report(test_result, category.priority)
                
                # Konsol çıktısı
                status = "✅" if success else "❌"
                print(f"  {status} Test {i:2d}: {test_case['input'][:40]:<40} → {response_time:.2f}s")
                
            except Exception as e:
                # Hata durumu
                test_result = TestResult(
                    test_type=category_name,
                    test_name=test_case.get("description", f"Test {i}"),
                    input_text=test_case["input"],
                    expected="Success",
                    actual="ERROR",
                    success=False,
                    response_time=0.0,
                    error=str(e)
                )
                self.test_results.append(test_result)
                self.create_issue_report(test_result, "CRITICAL")
                
                print(f"  ❌ Test {i:2d}: {test_case['input'][:40]:<40} → ERROR: {str(e)[:30]}")
    
    def evaluate_test_case(self, test_case: Dict, response: str, category: str) -> Tuple[bool, Dict]:
        """Test case'i değerlendir"""
        details = {}
        success_criteria = []
        
        # Kategori-özel değerlendirme
        if category == "claude_code_integration":
            details["claude_integration"] = "claude" in response.lower() or "code" in response.lower()
            success_criteria.append(details["claude_integration"])
            
        elif category == "gemini_enhanced_testing":
            details["gemini_usage"] = len(response) > 100 and any(keyword in response.lower() for keyword in ["analiz", "değerlendirme", "öneri"])
            success_criteria.append(details["gemini_usage"])
            
        elif category == "error_recovery_system":
            details["error_detection"] = any(keyword in response.lower() for keyword in ["hata", "error", "düzelt", "fix"])
            success_criteria.append(details["error_detection"])
            
        elif category == "performance_optimization":
            details["optimization_focus"] = any(keyword in response.lower() for keyword in ["optimize", "performans", "hız", "bellek"])
            success_criteria.append(details["optimization_focus"])
            
        elif category == "security_analysis":
            details["security_focus"] = any(keyword in response.lower() for keyword in ["güvenlik", "security", "açık", "vulnerability"])
            success_criteria.append(details["security_focus"])
            
        elif category == "ml_workflow_testing":
            details["ml_focus"] = any(keyword in response.lower() for keyword in ["model", "veri", "analiz", "makine öğrenmesi"])
            success_criteria.append(details["ml_focus"])
            
        elif category == "collaborative_development":
            details["collaboration_focus"] = any(keyword in response.lower() for keyword in ["review", "commit", "dokümantasyon", "git"])
            success_criteria.append(details["collaboration_focus"])
        
        # Genel başarı kriterleri
        details["response_quality"] = len(response.strip()) > 20
        details["no_errors"] = "error" not in response.lower() and "hata" not in response.lower()
        
        success_criteria.extend([details["response_quality"], details["no_errors"]])
        
        # Genel başarı durumu
        overall_success = all(success_criteria) if success_criteria else False
        
        return overall_success, details
    
    def create_issue_report(self, test_result: TestResult, severity: str):
        """Başarısız test için issue raporu oluştur"""
        issue_id = f"ISSUE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.issue_reports):03d}"
        
        issue = IssueReport(
            issue_id=issue_id,
            category=test_result.test_type,
            severity=severity,
            title=f"Test Failure: {test_result.test_name}",
            description=f"Test failed for input: '{test_result.input_text}'",
            test_input=test_result.input_text,
            expected_behavior=str(test_result.expected),
            actual_behavior=str(test_result.actual),
            error_trace=test_result.error,
            suggested_fixes=[],
            claude_analysis=None,
            timestamp=datetime.now().isoformat(),
            status="OPEN"
        )
        
        # Claude Analysis isteyeceğiz
        issue.suggested_fixes = self.generate_fix_suggestions(test_result)
        
        self.issue_reports.append(issue)
    
    def generate_fix_suggestions(self, test_result: TestResult) -> List[str]:
        """Test sonucuna göre düzeltme önerileri oluştur"""
        suggestions = []
        
        if test_result.test_type == "claude_code_integration":
            suggestions.extend([
                "Claude Code API entegrasyonunu kontrol et",
                "Claude Code komutlarının doğru formatını kullan",
                "Export fonksiyonlarını Claude Code uyumlu hale getir"
            ])
        elif test_result.test_type == "gemini_enhanced_testing":
            suggestions.extend([
                "Gemini API key'ini kontrol et",
                "Gemini model response parsing'i düzelt",
                "Test scenario generation logic'ini gözden geçir"
            ])
        elif test_result.test_type == "error_recovery_system":
            suggestions.extend([
                "Error detection algoritmasını iyileştir",
                "Auto-fix mechanisms'leri implement et",
                "Error handling robustness'ı artır"
            ])
        
        # Genel öneriler
        suggestions.extend([
            "Test case validation logic'ini gözden geçir",
            "Response parsing accuracy'sini artır",
            "Error logging mechanisms'leri ekle"
        ])
        
        return suggestions
    
    def generate_issue_reports(self):
        """Issue raporlarını ayrı dosyaya kaydet"""
        if not self.issue_reports:
            print("✅ No issues found!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Issue raporları için JSON dosyası
        issues_data = {
            "report_metadata": {
                "generation_time": datetime.now().isoformat(),
                "total_issues": len(self.issue_reports),
                "severity_breakdown": self.get_severity_breakdown(),
                "category_breakdown": self.get_category_breakdown()
            },
            "issues": [asdict(issue) for issue in self.issue_reports],
            "fix_recommendations": self.generate_global_fix_recommendations()
        }
        
        issues_file = f"issue_reports_{timestamp}.json"
        with open(issues_file, 'w', encoding='utf-8') as f:
            json.dump(issues_data, f, indent=2, ensure_ascii=False)
        
        # Issue Summary dosyası (Claude Code için)
        summary_file = f"issue_summary_{timestamp}.md"
        self.create_issue_summary_markdown(summary_file)
        
        print(f"\n📋 ISSUE REPORTS GENERATED")
        print("=" * 50)
        print(f"📁 Detailed Issues: {issues_file}")
        print(f"📄 Summary Report: {summary_file}")
        print(f"🚨 Total Issues: {len(self.issue_reports)}")
        print(f"⚠️ Critical Issues: {len([i for i in self.issue_reports if i.severity == 'CRITICAL'])}")
    
    def get_severity_breakdown(self) -> Dict[str, int]:
        """Issue severity breakdown"""
        breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in self.issue_reports:
            breakdown[issue.severity] = breakdown.get(issue.severity, 0) + 1
        return breakdown
    
    def get_category_breakdown(self) -> Dict[str, int]:
        """Issue category breakdown"""
        breakdown = {}
        for issue in self.issue_reports:
            breakdown[issue.category] = breakdown.get(issue.category, 0) + 1
        return breakdown
    
    def generate_global_fix_recommendations(self) -> List[str]:
        """Global düzeltme önerileri"""
        return [
            "Claude Code integration'ı için API wrapper'ları geliştir",
            "Gemini response parsing'i için robust error handling ekle",
            "Test evaluation criteria'larını daha spesifik hale getir",
            "Automated fix suggestions için AI model entegrasyonu ekle",
            "Real-time issue tracking dashboard oluştur"
        ]
    
    def create_issue_summary_markdown(self, filename: str):
        """Claude Code için markdown issue summary'si oluştur"""
        content = f"""# 🚨 Issue Report Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Overview
- **Total Issues:** {len(self.issue_reports)}
- **Critical Issues:** {len([i for i in self.issue_reports if i.severity == 'CRITICAL'])}
- **High Priority Issues:** {len([i for i in self.issue_reports if i.severity == 'HIGH'])}

## 🎯 Priority Issues

"""
        
        # Critical ve High priority issue'ları listele
        priority_issues = [i for i in self.issue_reports if i.severity in ['CRITICAL', 'HIGH']]
        for issue in priority_issues[:5]:  # İlk 5 priority issue
            content += f"""### {issue.severity} - {issue.title}
- **Category:** {issue.category}
- **Input:** `{issue.test_input}`
- **Expected:** {issue.expected_behavior}
- **Actual:** {issue.actual_behavior}
- **Suggestions:** {', '.join(issue.suggested_fixes[:2])}

"""
        
        content += f"""## 🔧 Claude Code Fix Commands

```bash
# Analyze this issue report with Claude Code
claude-code analyze {filename}

# Get specific fix suggestions
claude-code fix --category="{self.issue_reports[0].category if self.issue_reports else 'general'}"

# Run automated tests after fixes
python tools/advanced_test_categories.py --category=all
```

## 📈 Next Steps
1. Review critical issues first
2. Implement suggested fixes
3. Re-run tests to verify fixes
4. Update test cases based on findings
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def export_claude_integration_data(self):
        """Claude Code entegrasyonu için veri export et"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        claude_data = {
            "claude_integration": {
                "export_time": datetime.now().isoformat(),
                "test_results_summary": {
                    "total_tests": len(self.test_results),
                    "passed_tests": sum(1 for r in self.test_results if r.success),
                    "failed_tests": sum(1 for r in self.test_results if not r.success),
                    "success_rate": (sum(1 for r in self.test_results if r.success) / len(self.test_results)) * 100 if self.test_results else 0
                },
                "issue_analysis": {
                    "total_issues": len(self.issue_reports),
                    "by_severity": self.get_severity_breakdown(),
                    "by_category": self.get_category_breakdown()
                },
                "claude_commands": self.generate_claude_commands(),
                "analysis_prompts": [
                    "Analyze the failed test patterns and identify root causes",
                    "Suggest code improvements based on test failures",
                    "Review test case coverage and recommend additional scenarios",
                    "Optimize performance based on response time analysis",
                    "Identify security issues from test results"
                ]
            }
        }
        
        claude_file = f"claude_integration_{timestamp}.json"
        with open(claude_file, 'w', encoding='utf-8') as f:
            json.dump(claude_data, f, indent=2, ensure_ascii=False)
        
        print(f"🧠 Claude Code integration data exported: {claude_file}")
        return claude_file
    
    def generate_claude_commands(self) -> List[str]:
        """Claude Code komutları oluştur"""
        commands = [
            "claude-code analyze tools/terminal_agent.py",
            "claude-code review --focus=error-handling",
            "claude-code optimize --target=response-time",
            "claude-code test --coverage=advanced-categories"
        ]
        
        # Issue'lara göre özel komutlar
        if any(i.category == "claude_code_integration" for i in self.issue_reports):
            commands.append("claude-code fix --integration-issues")
        
        if any(i.category == "security_analysis" for i in self.issue_reports):
            commands.append("claude-code security-scan")
        
        return commands
    
    def create_claude_fix_commands(self) -> str:
        """Claude Code fix komutları oluştur"""
        fix_script = f"""#!/bin/bash
# 🔧 CLAUDE CODE AUTOMATED FIX SCRIPT
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🧠 Starting Claude Code automated fixes..."

# Analyze current issues
echo "📊 Analyzing issues..."
"""

        for issue in self.issue_reports[:3]:  # İlk 3 kritik issue
            fix_script += f"""
# Fix for: {issue.title}
echo "🔧 Fixing: {issue.title}"
# claude-code fix --issue="{issue.issue_id}" --category="{issue.category}"
"""
        
        fix_script += """
# Re-run tests to verify fixes
echo "🧪 Running verification tests..."
python tools/advanced_test_categories.py --verify-fixes

echo "✅ Claude Code fixes completed!"
"""
        
        script_file = f"claude_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(fix_script)
        
        os.chmod(script_file, 0o755)  # Make executable
        
        print(f"🔧 Claude fix script created: {script_file}")
        return script_file

def main():
    """Ana test sistemi"""
    print("🧪 ADVANCED TEST CATEGORIES SYSTEM")
    print("🎯 Claude Code Integration + Gemini Enhanced Testing")
    print("=" * 80)
    
    try:
        # Test sistemini başlat
        test_system = AdvancedTestCategoriesSystem()
        
        # Tüm kategorileri test et
        fix_script = test_system.run_advanced_category_tests()
        
        print(f"\n🎉 ADVANCED TESTING COMPLETED!")
        print(f"🔧 Fix script: {fix_script}")
        print(f"📋 Issue reports generated in separate files")
        print(f"🧠 Ready for Claude Code analysis and fixes")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ADVANCED TESTING FAILED!")
        print(f"🚨 Error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())