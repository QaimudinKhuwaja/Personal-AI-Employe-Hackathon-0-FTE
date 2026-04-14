"""
Silver Tier Verification Script

Verifies all Silver Tier components are properly set up and ready to use.

Usage:
    python verify_silver_tier.py
"""

import os
import sys
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_check(name, status, message=""):
    icon = "[OK]" if status else "[FAIL]"
    color = Colors.GREEN if status else Colors.RED
    print(f"{color}{icon} {name}{Colors.RESET}")
    if message:
        print(f"  {message}")

def check_file(filepath, description):
    """Check if a file exists."""
    exists = Path(filepath).exists()
    print_check(f"{description}: {filepath}", exists)
    return exists

def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print_check(f"{description}: {module_name}", True)
        return True
    except ImportError as e:
        print_check(f"{description}: {module_name}", False, str(e))
        return False

def check_directory(dirpath, description):
    """Check if a directory exists."""
    exists = Path(dirpath).is_dir()
    print_check(f"{description}: {dirpath}", exists)
    return exists

def main():
    print_header("SILVER TIER VERIFICATION")
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / 'scripts'
    vault_dir = project_root / 'AI_Employee_Vault'
    
    all_passed = True
    
    # Check Python version
    print_header("1. PYTHON ENVIRONMENT")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_check(f"Python version: {python_version}", sys.version_info >= (3, 10))
    
    # Check required packages
    print_header("2. REQUIRED PACKAGES")
    
    packages = [
        ('google.oauth2.credentials', 'Google Auth'),
        ('googleapiclient.discovery', 'Gmail API Client'),
        ('playwright.sync_api', 'Playwright'),
    ]
    
    for package, description in packages:
        try:
            __import__(package)
            print_check(f"{description}", True)
        except ImportError:
            print_check(f"{description}", False, "Package not installed")
            all_passed = False
    
    # Check project structure
    print_header("3. PROJECT STRUCTURE")
    
    directories = [
        (vault_dir, "Obsidian Vault"),
        (vault_dir / 'Needs_Action', "Needs Action Folder"),
        (vault_dir / 'Done', "Done Folder"),
        (vault_dir / 'Logs', "Logs Folder"),
        (scripts_dir, "Scripts Directory"),
    ]
    
    for dirpath, description in directories:
        if not check_directory(dirpath, description):
            all_passed = False
    
    # Check script files
    print_header("4. SCRIPT FILES")
    
    scripts = [
        (scripts_dir / 'gmail_watcher.py', "Gmail Watcher"),
        (scripts_dir / 'linkedin_poster.py', "LinkedIn Poster"),
        (scripts_dir / 'filesystem_watcher.py', "File System Watcher"),
        (scripts_dir / 'orchestrator.py', "Orchestrator"),
        (scripts_dir / 'base_watcher.py', "Base Watcher"),
    ]
    
    for script_path, description in scripts:
        if not check_file(script_path, description):
            all_passed = False
    
    # Check credentials
    print_header("5. CREDENTIALS & CONFIGURATION")
    
    credentials_file = project_root / 'credentials.json'
    if check_file(credentials_file, "Gmail Credentials"):
        print_check("  credentials.json exists", True)
    else:
        print_check("  credentials.json missing", False)
        all_passed = False
    
    # Check vault files
    print_header("6. VAULT FILES")
    
    vault_files = [
        (vault_dir / 'Dashboard.md', "Dashboard"),
        (vault_dir / 'Company_Handbook.md', "Company Handbook"),
        (vault_dir / 'Business_Goals.md', "Business Goals"),
    ]
    
    for file_path, description in vault_files:
        if not check_file(file_path, description):
            all_passed = False
    
    # Check imports
    print_header("7. MODULE IMPORTS")
    
    sys.path.insert(0, str(scripts_dir))
    
    imports = [
        ('gmail_watcher', 'Gmail Watcher Module'),
        ('linkedin_poster', 'LinkedIn Poster Module'),
        ('filesystem_watcher', 'File System Watcher Module'),
        ('orchestrator', 'Orchestrator Module'),
    ]
    
    for module_name, description in imports:
        if not check_import(module_name, description):
            all_passed = False
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}[OK] ALL CHECKS PASSED!{Colors.RESET}\n")
        print("Silver Tier is ready to use!")
        print("\nNext steps:")
        print("1. Authenticate Gmail:")
        print(f"   cd {project_root}")
        print("   python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json --auth-only")
        print("\n2. Setup LinkedIn session:")
        print("   python scripts/linkedin_poster.py --vault AI_Employee_Vault --setup-session")
        print("\n3. Start the watchers (3 terminals):")
        print("   Terminal 1: python scripts/gmail_watcher.py AI_Employee_Vault --credentials credentials.json")
        print("   Terminal 2: python scripts/filesystem_watcher.py AI_Employee_Vault")
        print("   Terminal 3: python scripts/orchestrator.py AI_Employee_Vault")
    else:
        print(f"{Colors.RED}{Colors.BOLD}[FAIL] SOME CHECKS FAILED{Colors.RESET}\n")
        print("Please review the failed checks above and fix them before proceeding.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install google-auth google-auth-oauthlib google-api-python-client playwright")
        print("  - Install Playwright browsers: playwright install chromium")
        print("  - Ensure credentials.json exists in the project root")
    
    print()
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
