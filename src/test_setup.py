#!/usr/bin/env python3
"""
Quick test script to verify SUMO and TraCI setup.

This script performs basic checks before running the full simulation.
"""

import os
import sys
from pathlib import Path

def check_sumo_home():
    """Check if SUMO_HOME is set."""
    print("1. Checking SUMO_HOME environment variable...")
    if 'SUMO_HOME' in os.environ:
        sumo_home = os.environ['SUMO_HOME']
        print(f"   ✓ SUMO_HOME is set: {sumo_home}")
        return True
    else:
        print("   ✗ SUMO_HOME is not set!")
        print("   Please set it with: export SUMO_HOME=/path/to/sumo")
        return False

def check_traci():
    """Check if TraCI can be imported."""
    print("\n2. Checking TraCI import...")
    try:
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        import traci
        print(f"   ✓ TraCI imported successfully")
        print(f"   TraCI version: {traci.__version__ if hasattr(traci, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print(f"   ✗ Failed to import TraCI: {e}")
        return False

def check_sumo_binary():
    """Check if SUMO binaries are available."""
    print("\n3. Checking SUMO binaries...")
    binaries = ['sumo', 'sumo-gui']
    found = []
    
    for binary in binaries:
        result = os.system(f"which {binary} > /dev/null 2>&1")
        if result == 0:
            print(f"   ✓ {binary} found")
            found.append(binary)
        else:
            print(f"   ✗ {binary} not found in PATH")
    
    return len(found) > 0

def check_config_files():
    """Check if SUMO configuration files exist."""
    print("\n4. Checking SUMO configuration files...")
    
    project_root = Path(__file__).parent.parent
    files_to_check = [
        'sumo/simulation.sumocfg',
        'sumo/network.net.xml',
        'sumo/routes.rou.xml'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✓ {file_path} exists")
        else:
            print(f"   ✗ {file_path} not found!")
            all_exist = False
    
    return all_exist

def check_python_version():
    """Check Python version."""
    print("\n5. Checking Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✓ Python version is compatible (>= 3.8)")
        return True
    else:
        print(f"   ✗ Python version should be >= 3.8")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("SUMO + TraCI Setup Verification")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_sumo_home(),
        check_traci(),
        check_sumo_binary(),
        check_config_files()
    ]
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"Checks passed: {passed}/{total}")
    
    if all(checks):
        print("\n✓ All checks passed! You're ready to run the simulation.")
        print("\nNext steps:")
        print("  1. Run with GUI:      python src/sumo_runner.py --gui")
        print("  2. Run headless:      python src/sumo_runner.py")
        print("  3. Run limited steps: python src/sumo_runner.py --max-steps 100")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
