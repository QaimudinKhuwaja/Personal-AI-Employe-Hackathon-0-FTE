"""
Gold Tier Verification Script

Tests all Gold Tier components to ensure they are properly installed and configured.

Usage:
    python scripts/verify_gold_tier.py
    python scripts/verify_gold_tier.py --verbose
    python scripts/verify_gold_tier.py --category odoo
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class GoldTierVerifier:
    """Verifies Gold Tier implementation."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.vault_path = self.project_root / 'AI_Employee_Vault'
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'categories': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def log(self, message: str, level: str = 'info'):
        """Log message."""
        prefix = {
            'info': '[INFO]',
            'success': '[OK]',
            'error': '[ERROR]',
            'warning': '[WARN]'
        }.get(level, '[-]')
        
        try:
            print(f"{prefix} {message}")
        except UnicodeEncodeError:
            # Fallback for Windows console
            print(f"{prefix} {message}".encode('cp1252', errors='replace').decode('cp1252'))
    
    def check_file_exists(self, path: Path, description: str) -> bool:
        """Check if file exists."""
        if path.exists():
            self.log(f"{description}: {path}", 'success')
            return True
        else:
            self.log(f"{description} missing: {path}", 'error')
            return False
    
    def check_directory_exists(self, path: Path, description: str) -> bool:
        """Check if directory exists."""
        if path.exists() and path.is_dir():
            self.log(f"{description}: {path}", 'success')
            return True
        else:
            self.log(f"{description} missing: {path}", 'error')
            return False
    
    def check_env_variable(self, name: str, required: bool = True) -> bool:
        """Check environment variable."""
        value = os.getenv(name)
        if value:
            self.log(f"{name}: Set", 'success')
            return True
        elif required:
            self.log(f"{name}: Not set (required)", 'error')
            return False
        else:
            self.log(f"{name}: Not set (optional)", 'warning')
            return True
    
    def verify_odoo_integration(self) -> Dict:
        """Verify Odoo integration."""
        self.log("\n🔍 Verifying Odoo Integration...", 'info')
        
        result = {
            'name': 'Odoo Integration',
            'checks': [],
            'passed': 0,
            'failed': 0
        }
        
        # Check docker-compose.yml
        check = self.check_file_exists(
            self.project_root / 'docker-compose.yml',
            'Docker Compose file'
        )
        result['checks'].append(('docker-compose.yml', check))
        result['passed' if check else 'failed'] += 1
        
        # Check odoo-config
        check = self.check_directory_exists(
            self.project_root / 'odoo-config',
            'Odoo config directory'
        )
        result['checks'].append(('odoo-config/', check))
        result['passed' if check else 'failed'] += 1
        
        # Check odoo_connector.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'odoo_connector.py',
            'Odoo connector script'
        )
        result['checks'].append(('odoo_connector.py', check))
        result['passed' if check else 'failed'] += 1
        
        # Check Odoo MCP server
        check = self.check_file_exists(
            self.project_root / 'mcp-servers' / 'odoo-mcp' / 'index.js',
            'Odoo MCP server'
        )
        result['checks'].append(('odoo-mcp/index.js', check))
        result['passed' if check else 'failed'] += 1
        
        # Check Odoo skill
        check = self.check_file_exists(
            self.project_root / '.qwen' / 'skills' / 'odoo-connector' / 'SKILL.md',
            'Odoo agent skill'
        )
        result['checks'].append(('odoo-connector/SKILL.md', check))
        result['passed' if check else 'failed'] += 1
        
        # Check environment variables
        check = self.check_env_variable('ODOO_URL', required=False)
        result['checks'].append(('ODOO_URL env', check))
        if check:
            result['passed'] += 1
        else:
            result['failed'] += 1
        
        self.results['categories']['odoo'] = result
        return result
    
    def verify_facebook_integration(self) -> Dict:
        """Verify Facebook integration."""
        self.log("\n🔍 Verifying Facebook Integration...", 'info')
        
        result = {
            'name': 'Facebook Integration',
            'checks': [],
            'passed': 0,
            'failed': 0
        }
        
        # Check facebook_graph_poster.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'facebook_graph_poster.py',
            'Facebook Graph API poster'
        )
        result['checks'].append(('facebook_graph_poster.py', check))
        result['passed' if check else 'failed'] += 1
        
        # Check Facebook skill
        check = self.check_file_exists(
            self.project_root / '.qwen' / 'skills' / 'facebook-poster' / 'SKILL.md',
            'Facebook agent skill'
        )
        result['checks'].append(('facebook-poster/SKILL.md', check))
        result['passed' if check else 'failed'] += 1
        
        # Check setup guide
        check = self.check_file_exists(
            self.project_root / 'FACEBOOK_SETUP_GUIDE.md',
            'Facebook setup guide'
        )
        result['checks'].append(('FACEBOOK_SETUP_GUIDE.md', check))
        result['passed' if check else 'failed'] += 1
        
        # Check environment variables
        for var in ['FACEBOOK_PAGE_ACCESS_TOKEN', 'FACEBOOK_PAGE_ID']:
            check = self.check_env_variable(var, required=False)
            result['checks'].append((var, check))
            if check:
                result['passed'] += 1
            else:
                result['failed'] += 1
        
        self.results['categories']['facebook'] = result
        return result

    def verify_twitter_integration(self) -> Dict:
        """Verify Twitter/X integration."""
        self.log("\n🔍 Verifying Twitter/X Integration...", 'info')

        result = {
            'name': 'Twitter/X Integration',
            'checks': [],
            'passed': 0,
            'failed': 0
        }

        # Check twitter_poster.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'twitter_poster.py',
            'Twitter poster script'
        )
        result['checks'].append(('twitter_poster.py', check))
        result['passed' if check else 'failed'] += 1

        # Check Twitter skill
        check = self.check_file_exists(
            self.project_root / '.qwen' / 'skills' / 'twitter-poster' / 'SKILL.md',
            'Twitter agent skill'
        )
        result['checks'].append(('twitter-poster/SKILL.md', check))
        result['passed' if check else 'failed'] += 1

        # Check environment variables
        for var in ['TWITTER_BEARER_TOKEN', 'TWITTER_API_KEY']:
            check = self.check_env_variable(var, required=False)
            result['checks'].append((var, check))
            if check:
                result['passed'] += 1
            else:
                result['failed'] += 1

        self.results['categories']['twitter'] = result
        return result

    def verify_ceo_briefing(self) -> Dict:
        """Verify CEO Briefing generator."""
        self.log("\n🔍 Verifying CEO Briefing Generator...", 'info')
        
        result = {
            'name': 'CEO Briefing Generator',
            'checks': [],
            'passed': 0,
            'failed': 0
        }
        
        # Check ceo_briefing_generator.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'ceo_briefing_generator.py',
            'CEO Briefing generator script'
        )
        result['checks'].append(('ceo_briefing_generator.py', check))
        result['passed' if check else 'failed'] += 1
        
        # Check CEO briefing skill
        check = self.check_file_exists(
            self.project_root / '.qwen' / 'skills' / 'ceo-briefing' / 'SKILL.md',
            'CEO Briefing agent skill'
        )
        result['checks'].append(('ceo-briefing/SKILL.md', check))
        result['passed' if check else 'failed'] += 1
        
        # Check Briefings folder
        check = self.check_directory_exists(
            self.vault_path / 'Briefings',
            'Briefings folder'
        )
        result['checks'].append(('Briefings/', check))
        result['passed' if check else 'failed'] += 1
        
        self.results['categories']['ceo_briefing'] = result
        return result
    
    def verify_error_recovery(self) -> Dict:
        """Verify error recovery system."""
        self.log("\n🔍 Verifying Error Recovery System...", 'info')
        
        result = {
            'name': 'Error Recovery System',
            'checks': [],
            'passed': 0,
            'failed': 0
        }
        
        # Check retry_handler.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'retry_handler.py',
            'Retry handler script'
        )
        result['checks'].append(('retry_handler.py', check))
        result['passed' if check else 'failed'] += 1
        
        # Check audit_logger.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'audit_logger.py',
            'Audit logger script'
        )
        result['checks'].append(('audit_logger.py', check))
        result['passed' if check else 'failed'] += 1
        
        # Check health_checker.py
        check = self.check_file_exists(
            self.project_root / 'scripts' / 'health_checker.py',
            'Health checker script'
        )
        result['checks'].append(('health_checker.py', check))
        result['passed' if check else 'failed'] += 1
        
        # Check Quarantine folder
        check = self.check_directory_exists(
            self.vault_path / 'Quarantine',
            'Quarantine folder'
        )
        result['checks'].append(('Quarantine/', check))
        result['passed' if check else 'failed'] += 1
        
        self.results['categories']['error_recovery'] = result
        return result
    
    def verify_documentation(self) -> Dict:
        """Verify documentation."""
        self.log("\n🔍 Verifying Documentation...", 'info')
        
        result = {
            'name': 'Documentation',
            'checks': [],
            'passed': 0,
            'failed': 0
        }
        
        docs = [
            'GOLD_TIER_ARCHITECTURE.md',
            'GOLD_TIER_COMPLETE.md',
            'ODOO_DOCKER_SETUP.md',
            'FACEBOOK_SETUP_GUIDE.md'
        ]
        
        for doc in docs:
            check = self.check_file_exists(
                self.project_root / doc,
                f'{doc}'
            )
            result['checks'].append((doc, check))
            result['passed' if check else 'failed'] += 1
        
        self.results['categories']['documentation'] = result
        return result
    
    def run_functional_tests(self) -> Dict:
        """Run functional tests."""
        self.log("\n🧪 Running Functional Tests...", 'info')
        
        result = {
            'name': 'Functional Tests',
            'tests': [],
            'passed': 0,
            'failed': 0
        }
        
        # Test audit logger
        self.log("Testing audit logger...", 'info')
        try:
            sys.path.insert(0, str(self.project_root / 'scripts'))
            from audit_logger import AuditLogger
            
            logger = AuditLogger()
            log_id = logger.log_action(
                action_type='gold_tier_verification',
                actor='verify_gold_tier.py',
                parameters={'test': True},
                result='success'
            )
            
            if log_id:
                self.log("Audit logger test: PASSED", 'success')
                result['tests'].append(('audit_logger', True))
                result['passed'] += 1
            else:
                self.log("Audit logger test: FAILED", 'error')
                result['tests'].append(('audit_logger', False))
                result['failed'] += 1
        except Exception as e:
            self.log(f"Audit logger test failed: {e}", 'error')
            result['tests'].append(('audit_logger', False))
            result['failed'] += 1
        
        # Test retry handler
        self.log("Testing retry handler...", 'info')
        try:
            from retry_handler import with_retry, RetryError
            
            @with_retry(max_attempts=2, base_delay=0.1)
            def test_func():
                return "success"
            
            result_val = test_func()
            if result_val == "success":
                self.log("Retry handler test: PASSED", 'success')
                result['tests'].append(('retry_handler', True))
                result['passed'] += 1
            else:
                self.log("Retry handler test: FAILED", 'error')
                result['tests'].append(('retry_handler', False))
                result['failed'] += 1
        except Exception as e:
            self.log(f"Retry handler test failed: {e}", 'error')
            result['tests'].append(('retry_handler', False))
            result['failed'] += 1
        
        self.results['categories']['functional_tests'] = result
        return result
    
    def generate_report(self) -> str:
        """Generate verification report."""
        # Calculate summary
        for category in self.results['categories'].values():
            self.results['summary']['total'] += category['passed'] + category['failed']
            self.results['summary']['passed'] += category['passed']
            self.results['summary']['failed'] += category['failed']
        
        report = f"""
# Gold Tier Verification Report

**Generated:** {self.results['timestamp']}

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Checks** | {self.results['summary']['total']} |
| **Passed** | {self.results['summary']['passed']} |
| **Failed** | {self.results['summary']['failed']} |
| **Success Rate** | {(self.results['summary']['passed'] / max(1, self.results['summary']['total'])) * 100:.1f}% |

---

## Detailed Results

"""
        
        for category_name, category_data in self.results['categories'].items():
            report += f"\n### {category_data['name']}\n\n"
            
            if 'checks' in category_data:
                report += "| Check | Status |\n"
                report += "|-------|--------|\n"
                for check_name, passed in category_data['checks']:
                    status = '✅' if passed else '❌'
                    report += f"| {check_name} | {status} |\n"
            
            if 'tests' in category_data:
                report += "| Test | Status |\n"
                report += "|------|--------|\n"
                for test_name, passed in category_data['tests']:
                    status = '✅' if passed else '❌'
                    report += f"| {test_name} | {status} |\n"
            
            report += f"\n**Score:** {category_data['passed']}/{category_data['passed'] + category_data['failed']} passed\n"
        
        # Overall status
        success_rate = (self.results['summary']['passed'] / max(1, self.results['summary']['total'])) * 100
        
        if success_rate >= 90:
            overall = "✅ GOLD TIER VERIFIED"
        elif success_rate >= 70:
            overall = "⚠️ PARTIALLY COMPLETE"
        else:
            overall = "❌ NEEDS WORK"
        
        report += f"""
---

## Overall Status

**{overall}**

Success Rate: {success_rate:.1f}%

---

*Generated by verify_gold_tier.py*
"""
        
        return report
    
    def verify(self) -> bool:
        """Run all verifications."""
        # Set UTF-8 encoding for Windows console
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
        print("=" * 60)
        print("GOLD TIER VERIFICATION")
        print("=" * 60)
        
        # Run all verifications
        self.verify_odoo_integration()
        self.verify_facebook_integration()
        self.verify_twitter_integration()
        self.verify_ceo_briefing()
        self.verify_error_recovery()
        self.verify_documentation()
        self.run_functional_tests()
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_file = self.vault_path / 'Updates' / f'gold_tier_verification_{datetime.now().strftime("%Y-%m-%d")}.md'
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report, encoding='utf-8')
        
        # Print report
        print(report)
        
        self.log(f"\n📄 Full report saved to: {report_file}", 'info')
        
        # Return success status
        return self.results['summary']['failed'] == 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gold Tier Verification')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--category', '-c', type=str, help='Verify specific category')
    parser.add_argument('--output', '-o', type=str, help='Output file for report')
    
    args = parser.parse_args()
    
    # Change to project root
    os.chdir(Path(__file__).parent.parent)
    
    # Run verification
    verifier = GoldTierVerifier(verbose=args.verbose)
    success = verifier.verify()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
