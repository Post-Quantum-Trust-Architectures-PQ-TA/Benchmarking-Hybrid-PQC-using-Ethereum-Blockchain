"""
Check if all required dependencies are installed
"""
import sys

def check_dependency(module_name, import_name=None):
    """Check if a dependency is available"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def main():
    """Check all dependencies"""
    print("="*70)
    print("  DEPENDENCY CHECK")
    print("="*70)
    print(f"\nPython version: {sys.version}")
    print()
    
    dependencies = [
        ('web3', 'web3'),
        ('py-solc-x', 'solcx'),
        ('quantcrypt', 'quantcrypt'),
        ('cryptography', 'cryptography'),
        ('matplotlib', 'matplotlib'),
        ('numpy', 'numpy'),
        ('tqdm', 'tqdm'),
        ('pytest', 'pytest'),
    ]
    
    optional = [
        ('ecdsa', 'ecdsa', 'Alternative ECDSA library'),
        ('psutil', 'psutil', 'Advanced metrics (memory, CPU)'),
    ]
    
    print("Required Dependencies:")
    print("-" * 70)
    all_ok = True
    for package, module, *rest in dependencies:
        available, error = check_dependency(package, module)
        status = "[OK]" if available else "[MISSING]"
        print(f"{status} {package:<20} {module}")
        if not available:
            all_ok = False
            print(f"         Install with: pip install {package}")
    
    print("\nOptional Dependencies:")
    print("-" * 70)
    for package, module, description in optional:
        available, error = check_dependency(package, module)
        status = "[OK]" if available else "[OPTIONAL]"
        print(f"{status} {package:<20} {module:<15} {description}")
    
    print("\n" + "="*70)
    if all_ok:
        print("[SUCCESS] All required dependencies are installed!")
    else:
        print("[WARNING] Some required dependencies are missing")
        print("          Install with: pip install -r requirements.txt")
    print("="*70)

if __name__ == "__main__":
    main()

