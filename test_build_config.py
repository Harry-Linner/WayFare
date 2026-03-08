#!/usr/bin/env python3
"""
Test script to validate the PyInstaller build configuration

This script checks that:
1. build.spec file is valid Python
2. All referenced files exist
3. Hidden imports can be resolved
"""

import sys
from pathlib import Path


def test_spec_file():
    """Test that build.spec is valid"""
    print("Testing build.spec file...")
    
    spec_path = Path("build.spec")
    if not spec_path.exists():
        print("✗ build.spec not found")
        return False
    
    try:
        # Try to compile the spec file
        with open(spec_path, 'r') as f:
            spec_content = f.read()
        
        compile(spec_content, 'build.spec', 'exec')
        print("✓ build.spec is valid Python")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in build.spec: {e}")
        return False


def test_entry_point():
    """Test that the entry point exists"""
    print("\nTesting entry point...")
    
    entry_point = Path("wayfare/main.py")
    if not entry_point.exists():
        print(f"✗ Entry point not found: {entry_point}")
        return False
    
    print(f"✓ Entry point exists: {entry_point}")
    return True


def test_data_files():
    """Test that referenced data files exist"""
    print("\nTesting data files...")
    
    # Check for config.yaml
    config_file = Path("config.yaml")
    if config_file.exists():
        print(f"✓ Config file exists: {config_file}")
    else:
        print(f"⚠ Config file not found: {config_file} (optional)")
    
    # Check for models directory
    models_dir = Path("wayfare/models")
    if models_dir.exists():
        onnx_files = list(models_dir.glob("*.onnx"))
        if onnx_files:
            print(f"✓ Found {len(onnx_files)} ONNX model(s)")
        else:
            print("⚠ No ONNX models found (will need to be added)")
    else:
        print("⚠ Models directory not found (will need to be created)")
    
    return True


def test_hidden_imports():
    """Test that hidden imports can be resolved"""
    print("\nTesting hidden imports...")
    
    critical_imports = [
        'aiosqlite',
        'pydantic',
        'yaml',
        'blake3',
        'numpy',
    ]
    
    optional_imports = [
        'onnxruntime',
        'qdrant_client',
        'transformers',
        'fitz',  # PyMuPDF
        'markdown_it',
        'litellm',
    ]
    
    all_ok = True
    
    for module_name in critical_imports:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError:
            print(f"✗ {module_name} (CRITICAL - required)")
            all_ok = False
    
    for module_name in optional_imports:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError:
            print(f"⚠ {module_name} (optional - may be needed)")
    
    return all_ok


def test_wayfare_imports():
    """Test that wayfare modules can be imported"""
    print("\nTesting wayfare module imports...")
    
    wayfare_modules = [
        'wayfare',
        'wayfare.config',
        'wayfare.db',
        'wayfare.embedding',
        'wayfare.vector_store',
        'wayfare.document_parser',
        'wayfare.llm_provider',
        'wayfare.context_builder',
        'wayfare.annotation_generator',
        'wayfare.behavior_analyzer',
        'wayfare.ipc',
        'wayfare.logging',
        'wayfare.errors',
    ]
    
    all_ok = True
    
    for module_name in wayfare_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")
            all_ok = False
    
    return all_ok


def main():
    """Run all tests"""
    print("=" * 60)
    print("  PyInstaller Build Configuration Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Spec file", test_spec_file()))
    results.append(("Entry point", test_entry_point()))
    results.append(("Data files", test_data_files()))
    results.append(("Hidden imports", test_hidden_imports()))
    results.append(("WayFare imports", test_wayfare_imports()))
    
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        print("\nYou can now build the executable:")
        print("  1. Install PyInstaller: pip install pyinstaller")
        print("  2. Run build script: python build.py --clean")
        return 0
    else:
        print("\n✗ Some tests failed")
        print("\nPlease fix the issues above before building.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
