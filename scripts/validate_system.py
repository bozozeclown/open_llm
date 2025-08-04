#!/usr/bin/env python3
"""
System validation script.
Run this script to validate the entire system configuration.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.validation import validate_system, print_validation_results

def main():
    """Main validation function."""
    print("🔍 Starting system validation...")
    print()
    
    # Run validation
    results = validate_system()
    
    # Print results
    print_validation_results(results)
    
    # Print summary
    print("\n" + "="*50)
    if results['status'] == "healthy":
        print("✅ System validation completed successfully!")
        print("🎉 All systems are operational.")
    elif results['status'] == "unhealthy":
        print("❌ System validation failed!")
        print("🔧 Please address the issues above before proceeding.")
        sys.exit(1)
    else:
        print("⚠️  System validation completed with warnings.")
        print("📝 Please review the warnings above.")
    
    print("="*50)

if __name__ == "__main__":
    main()