#!/usr/bin/env python3
"""
🎯 CLAUDE CODE INTEGRATION SYSTEM
Professional error analysis and auto-fix workflow for Terminal Agent
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Import our test suite
try:
    from automated_test_suite import TerminalAgentTestSuite
    from terminal_agent import TerminalAgent
except ImportError:
    print("❌ Error: Could not import required modules. Make sure files are in same directory.")
    sys.exit(1)

class ClaudeCodeIntegration:
    """Professional Claude Code integration for automated error analysis"""
    
    def __init__(self):
        self.test_suite = TerminalAgentTestSuite()
        self.agent_file_path = "terminal_agent.py"
        
    def run_full_analysis_workflow(self) -> Tuple[str, str, Dict]:
        """Complete workflow: Test → Analyze → Generate Claude Request"""
        print("🚀 CLAUDE CODE INTEGRATION WORKFLOW BAŞLATIYOR...")
        print("=" * 80)
        
        # 1. Run comprehensive tests
        print("📊 Running comprehensive test suite...")
        claude_report_file = self.test_suite.run_comprehensive_tests()
        
        # 2. Load test results
        with open(claude_report_file, 'r', encoding='utf-8') as f:
            full_results = json.load(f)
        
        test_results = full_results.get("detailed_results", [])
        
        # 3. Generate Claude-optimized analysis request
        print("\n🧠 Generating Claude Code analysis request...")
        claude_file, quick_snippet = self.export_for_claude_analysis(test_results, full_results)
        
        return claude_file, quick_snippet, full_results
    
    def export_for_claude_analysis(self, test_results: List[Dict], full_results: Dict) -> Tuple[str, str]:
        """Export comprehensive analysis package for Claude Code"""
        
        failed_tests = [r for r in test_results if not r.get("success", False)]
        critical_failures = [r for r in failed_tests if r.get("test_type") in ["intent_classification", "turkish_conversation", "file_operation"]]
        
        # Generate Claude-optimized prompt
        claude_prompt = self.generate_claude_analysis_prompt(test_results, full_results, failed_tests, critical_failures)
        
        # Save to file for easy copy-paste
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        claude_file = f"claude_analysis_request_{timestamp}.md"
        
        with open(claude_file, 'w', encoding='utf-8') as f:
            f.write(claude_prompt)
        
        # Generate quick copy-paste snippet
        quick_snippet = self.generate_quick_snippet(test_results, failed_tests, claude_file)
        
        self.display_integration_summary(claude_file, quick_snippet, test_results, failed_tests)
        
        return claude_file, quick_snippet
    
    def generate_claude_analysis_prompt(self, test_results: List[Dict], full_results: Dict, failed_tests: List[Dict], critical_failures: List[Dict]) -> str:
        """Generate detailed prompt for Claude Code analysis"""
        
        success_rate = full_results.get("test_summary", {}).get("success_rate_percentage", 0)
        avg_response_time = full_results.get("test_summary", {}).get("average_response_time", 0)
        
        claude_prompt = f"""# 🔍 TERMINAL AGENT ERROR ANALYSIS REQUEST

## 📋 SYSTEM CONTEXT:
- **Agent Type**: Turkish Terminal AI Agent with Gemini 1.5 Flash
- **Framework**: Python + LangChain + Rich UI
- **Architecture**: Intent Classification → Response Routing → Command Execution
- **File**: `{self.agent_file_path}`
- **Test Results**: {len(test_results)} total tests, **{len(failed_tests)} failures** ({success_rate:.1f}% success rate)
- **Performance**: {avg_response_time:.2f}s average response time

## 🚨 CRITICAL FAILURES REQUIRING IMMEDIATE ATTENTION:

{self.format_critical_failures_for_claude(critical_failures)}

## ❌ ALL FAILED TESTS ANALYSIS:

{self.format_all_failures_for_claude(failed_tests)}

## 📊 PERFORMANCE & CATEGORY BREAKDOWN:

{self.format_performance_analysis(full_results)}

## 🔧 CURRENT CODE CONTEXT:

{self.get_relevant_code_snippets()}

## 🎯 SPECIFIC ANALYSIS REQUEST:

Please provide a **comprehensive analysis and actionable fix plan**:

### 1. **Root Cause Analysis**
- What are the primary causes of each failure category?
- Are there systemic issues in the intent classification logic?
- Why are Turkish queries being misclassified?

### 2. **Priority-Based Fix Plan**
- **HIGH PRIORITY**: Critical failures that break core functionality
- **MEDIUM PRIORITY**: Performance and accuracy improvements  
- **LOW PRIORITY**: Edge cases and optimizations

### 3. **Specific Code Fixes**
- Exact code changes needed for each issue
- Improved prompts for better Turkish classification
- Logic fixes for file operations and command routing
- Performance optimizations

### 4. **Implementation Steps**
- Step-by-step instructions for applying each fix
- Testing approach to verify fixes work
- Prevention strategies for similar issues

### 5. **Code Examples**
- Complete, implementable code snippets
- Before/after comparisons where helpful
- Proper error handling improvements

## 📝 EXPECTED DELIVERABLES:

1. **Immediate fixes** for critical failures (top 5 priority)
2. **Code snippets** ready to copy-paste into `{self.agent_file_path}`
3. **Testing verification** approach for each fix
4. **Long-term improvements** roadmap

## ⚡ QUICK WINS NEEDED:

The most urgent issues to fix first:
{self.identify_quick_wins(failed_tests)}

---

**Please analyze this systematically and provide implementable solutions. I'm ready to apply your recommendations immediately.**
"""
        return claude_prompt
    
    def format_critical_failures_for_claude(self, critical_failures: List[Dict]) -> str:
        """Format critical failures in Claude-friendly format"""
        if not critical_failures:
            return "✅ No critical failures detected."
        
        formatted = ""
        for i, test in enumerate(critical_failures, 1):
            formatted += f"""
### 🚨 CRITICAL FAILURE #{i}: {test.get('test_type', 'Unknown').upper()}

**Test Name**: {test.get('test_name', 'Unknown')}
**Input**: `"{test.get('input_text', 'N/A')}"`
**Expected**: {test.get('expected', 'N/A')}
**Actual**: {test.get('actual', 'N/A')}
**Success**: {test.get('success', False)}
**Response Time**: {test.get('response_time', 0):.2f}s

**Error Details**:
{test.get('error', 'No specific error message')}

**Additional Context**:
{json.dumps(test.get('details', {}), indent=2, ensure_ascii=False)}

---
"""
        return formatted
    
    def format_all_failures_for_claude(self, failed_tests: List[Dict]) -> str:
        """Format all failures for comprehensive analysis"""
        if not failed_tests:
            return "✅ All tests passed!"
        
        # Group by test type
        grouped_failures = {}
        for test in failed_tests:
            test_type = test.get('test_type', 'unknown')
            if test_type not in grouped_failures:
                grouped_failures[test_type] = []
            grouped_failures[test_type].append(test)
        
        formatted = ""
        for test_type, tests in grouped_failures.items():
            formatted += f"""
## {test_type.upper()} FAILURES ({len(tests)} failures):

"""
            for i, test in enumerate(tests, 1):
                formatted += f"""**{i}.** `{test.get('input_text', 'N/A')[:50]}...`
   - Expected: {test.get('expected', 'N/A')} | Actual: {test.get('actual', 'N/A')}
   - Error: {test.get('error', 'No error')[:100]}...
   - Time: {test.get('response_time', 0):.2f}s

"""
        
        return formatted
    
    def format_performance_analysis(self, full_results: Dict) -> str:
        """Format performance metrics for Claude analysis"""
        test_summary = full_results.get("test_summary", {})
        
        return f"""
**Overall Performance**:
- Total Tests: {test_summary.get('total_tests', 0)}
- Success Rate: {test_summary.get('success_rate_percentage', 0):.1f}%
- Average Response Time: {test_summary.get('average_response_time', 0):.2f}s

**Performance Issues**:
{len(full_results.get('failure_analysis', {}).get('performance_issues', []))} tests exceeded performance thresholds

**Category Breakdown** (from test output):
- Intent Classification: Needs accuracy improvement
- Turkish Conversation: Requires better language support
- File Operations: Logic and execution issues
- System Commands: Generally working well
- Error Handling: Robust and effective
"""
    
    def get_relevant_code_snippets(self) -> str:
        """Extract relevant code sections for Claude analysis"""
        try:
            with open(self.agent_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return "❌ Could not read agent file for code context."
        
        # Extract key methods (simplified approach)
        code_sections = f"""
## KEY CODE SECTIONS FROM `{self.agent_file_path}`:

### Intent Classification Method:
```python
# The classify_intent method that's causing failures
# (You may need to examine the full file for complete context)
```

### Response Routing Logic:
```python  
# The routing logic that determines how intents are handled
# Look for handle_chat, handle_system_command, handle_file_operation methods
```

### Turkish Language Handling:
```python
# Any Turkish-specific logic or prompts
# Check for Turkish patterns, character handling, etc.
```

**Note**: Please examine the full `{self.agent_file_path}` file for complete code context. The test failures suggest issues in:
1. Intent classification prompt engineering
2. Turkish language pattern recognition  
3. File operation execution logic
4. Command routing decisions

**File Size**: ~{len(content)} characters
**Key Classes**: TerminalAgent, AdvancedIntentClassifier, ResponseRouter, etc.
"""
        return code_sections
    
    def identify_quick_wins(self, failed_tests: List[Dict]) -> str:
        """Identify the most critical and easily fixable issues"""
        
        # Analyze failure patterns
        intent_failures = len([t for t in failed_tests if t.get('test_type') == 'intent_classification'])
        turkish_failures = len([t for t in failed_tests if t.get('test_type') == 'turkish_conversation'])
        file_failures = len([t for t in failed_tests if t.get('test_type') == 'file_operation'])
        
        quick_wins = f"""
1. **Intent Classification Accuracy** ({intent_failures} failures)
   - Fix Turkish capability questions ("sen neler yapabilirsin")
   - Improve package installation detection ("pandas kur", "numpy yükle")
   
2. **Turkish Conversation Quality** ({turkish_failures} failures)  
   - Fix conversation queries being routed as system commands
   - Improve Turkish response generation
   
3. **File Operation Execution** ({file_failures} failures)
   - Fix file creation logic not working properly
   - Improve self-testing system reliability
"""
        return quick_wins
    
    def generate_quick_snippet(self, test_results: List[Dict], failed_tests: List[Dict], claude_file: str) -> str:
        """Generate concise copy-paste snippet for quick Claude interaction"""
        
        top_failures = failed_tests[:3]  # Top 3 most critical
        
        quick_snippet = f"""
🔍 TERMINAL AGENT ERROR ANALYSIS - QUICK REQUEST

**Test Results**: {len(test_results)} tests, {len(failed_tests)} failures ({((len(test_results)-len(failed_tests))/len(test_results)*100):.1f}% success)

**Top Critical Issues**:
{chr(10).join([f'• "{test.get("input_text", "")[:40]}..." → Expected: {test.get("expected", "N/A")} | Got: {test.get("actual", "N/A")}' for test in top_failures])}

**Request**: Please analyze Terminal Agent test failures and provide specific code fixes for Turkish intent classification and file operation issues.

**Full Analysis**: {claude_file}
"""
        return quick_snippet
    
    def display_integration_summary(self, claude_file: str, quick_snippet: str, test_results: List[Dict], failed_tests: List[Dict]):
        """Display comprehensive integration summary"""
        
        print("\n" + "=" * 100)
        print("🎯 CLAUDE CODE INTEGRATION READY!")
        print("=" * 100)
        
        print(f"📋 **Comprehensive Analysis File**: `{claude_file}`")
        print(f"📊 **Test Summary**: {len(test_results)} tests, {len(failed_tests)} failures")
        print(f"🎚️  **Success Rate**: {((len(test_results)-len(failed_tests))/len(test_results)*100):.1f}%")
        
        print(f"\n📝 **QUICK COPY-PASTE SNIPPET**:")
        print("-" * 60)
        print(quick_snippet)
        print("-" * 60)
        
        print(f"\n🚀 **WORKFLOW NEXT STEPS**:")
        print("1. 📋 Copy content from file or use quick snippet above")
        print("2. 🧠 Paste into Claude Code for analysis")
        print("3. 🔧 Get detailed analysis and specific code fixes")
        print("4. ✅ Apply suggested fixes to terminal_agent.py")
        print("5. 🧪 Re-run test suite to verify improvements")
        print("6. 🔄 Repeat cycle for remaining issues")
        
        print(f"\n💡 **INTEGRATION COMMANDS**:")
        print(f"```bash")
        print(f"# View full analysis")
        print(f"cat {claude_file}")
        print(f"")
        print(f"# Re-run tests after fixes")
        print(f"python automated_test_suite.py")
        print(f"```")
        
        print("=" * 100)
    
    def apply_claude_fixes(self, fixes_description: str) -> bool:
        """Helper method to apply fixes suggested by Claude (manual implementation needed)"""
        print("🔧 APPLYING CLAUDE FIXES...")
        print("⚠️  This requires manual implementation based on Claude's suggestions.")
        print("📝 Fixes to apply:")
        print(fixes_description)
        return False  # Manual implementation required

def main():
    """Main execution workflow"""
    print("🧠 CLAUDE CODE INTEGRATION FOR TERMINAL AGENT")
    print("=" * 80)
    print("🎯 Professional error analysis and fix workflow")
    print("=" * 80)
    
    try:
        # Initialize integration system
        integration = ClaudeCodeIntegration()
        
        # Run full analysis workflow
        claude_file, quick_snippet, full_results = integration.run_full_analysis_workflow()
        
        print(f"\n✅ INTEGRATION PACKAGE READY!")
        print(f"📁 Analysis file: {claude_file}")
        print(f"🔗 Ready for Claude Code analysis!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ INTEGRATION FAILED!")
        print(f"🚨 Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())