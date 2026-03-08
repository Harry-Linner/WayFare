#!/usr/bin/env python3
"""
Build script for WayFare MVP Backend

This script automates the PyInstaller build process and performs validation checks.

Usage:
    python build.py [--clean] [--test]

Options:
    --clean     Clean build artifacts before building
    --test      Test the built executable after building
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Checking Dependencies")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} installed")
    except ImportError:
        print("✗ PyInstaller not found")
        print("\nPlease install PyInstaller:")
        print("  pip install pyinstaller")
        return False
    
    # Check if requirements.txt dependencies are installed
    try:
        import onnxruntime
        print(f"✓ onnxruntime {onnxruntime.__version__} installed")
    except ImportError:
        print("✗ onnxruntime not found")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False
    
    try:
        import qdrant_client
        print(f"✓ qdrant_client installed")
    except ImportError:
        print("✗ qdrant_client not found")
        return False
    
    try:
        import transformers
        print(f"✓ transformers {transformers.__version__} installed")
    except ImportError:
        print("✗ transformers not found")
        return False
    
    print("\n✓ All required dependencies are installed")
    return True


def check_models():
    """Check if ONNX models are available"""
    print_section("Checking ONNX Models")
    
    models_dir = Path("wayfare/models")
    onnx_files = list(models_dir.glob("*.onnx"))
    
    if not onnx_files:
        print("⚠ Warning: No ONNX model files found in wayfare/models/")
        print("\nThe embedding model is required for the backend to function.")
        print("Please download the model:")
        print("  1. Visit: https://huggingface.co/BAAI/bge-small-zh-v1.5")
        print("  2. Download the ONNX model file")
        print("  3. Place it in: wayfare/models/bge-small-zh-v1.5.onnx")
        print("\nContinuing build without model (you'll need to add it later)...")
        return False
    else:
        print(f"✓ Found {len(onnx_files)} ONNX model file(s):")
        for model in onnx_files:
            size_mb = model.stat().st_size / (1024 * 1024)
            print(f"  - {model.name} ({size_mb:.1f} MB)")
        return True


def clean_build():
    """Clean build artifacts"""
    print_section("Cleaning Build Artifacts")
    
    dirs_to_clean = ["build", "dist"]
    files_to_clean = ["wayfare-backend.spec"]
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"Removing {dir_name}/")
            shutil.rmtree(dir_name)
    
    for file_name in files_to_clean:
        if Path(file_name).exists():
            print(f"Removing {file_name}")
            Path(file_name).unlink()
    
    print("\n✓ Build artifacts cleaned")


def run_pyinstaller():
    """Run PyInstaller with build.spec"""
    print_section("Running PyInstaller")
    
    if not Path("build.spec").exists():
        print("✗ build.spec not found")
        return False
    
    print("Building executable with PyInstaller...")
    print("This may take several minutes...\n")
    
    try:
        result = subprocess.run(
            ["pyinstaller", "build.spec"],
            check=True,
            capture_output=False
        )
        print("\n✓ PyInstaller build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ PyInstaller build failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n✗ PyInstaller command not found")
        print("Please install PyInstaller: pip install pyinstaller")
        return False


def check_output():
    """Check if the output executable was created"""
    print_section("Checking Build Output")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("✗ dist/ directory not found")
        return False
    
    # Check for executable
    if sys.platform == 'win32':
        exe_name = "wayfare-backend.exe"
    else:
        exe_name = "wayfare-backend"
    
    exe_path = dist_dir / exe_name
    if not exe_path.exists():
        print(f"✗ Executable not found: {exe_path}")
        return False
    
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✓ Executable created: {exe_path}")
    print(f"  Size: {size_mb:.1f} MB")
    
    # Make executable on Unix-like systems
    if sys.platform != 'win32':
        os.chmod(exe_path, 0o755)
        print("  Permissions: Set to executable")
    
    return True


def test_executable():
    """Test the built executable"""
    print_section("Testing Executable")
    
    if sys.platform == 'win32':
        exe_name = "wayfare-backend.exe"
    else:
        exe_name = "wayfare-backend"
    
    exe_path = Path("dist") / exe_name
    
    if not exe_path.exists():
        print("✗ Executable not found")
        return False
    
    print("Testing executable with --version flag...")
    try:
        result = subprocess.run(
            [str(exe_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✓ Executable runs successfully")
            print(f"  Output: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Executable returned error code {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Executable timed out")
        return False
    except Exception as e:
        print(f"✗ Error testing executable: {e}")
        return False


def print_summary(success: bool, has_models: bool):
    """Print build summary"""
    print_section("Build Summary")
    
    if success:
        print("✓ Build completed successfully!")
        print("\nOutput location:")
        if sys.platform == 'win32':
            print("  dist/wayfare-backend.exe")
        else:
            print("  dist/wayfare-backend")
        
        if not has_models:
            print("\n⚠ Important: ONNX model not included in build")
            print("  You need to download and place the model file:")
            print("  1. Download from: https://huggingface.co/BAAI/bge-small-zh-v1.5")
            print("  2. Place in the same directory as the executable")
            print("  3. Update config.yaml to point to the model file")
        
        print("\nNext steps:")
        print("  1. Test the executable:")
        print("     ./dist/wayfare-backend --version")
        print("  2. Copy to your Tauri project:")
        print("     cp dist/wayfare-backend <tauri-project>/src-tauri/binaries/")
        print("  3. Update tauri.conf.json to reference the sidecar")
        
    else:
        print("✗ Build failed")
        print("\nPlease check the error messages above and try again.")


def main():
    """Main build function"""
    parser = argparse.ArgumentParser(
        description="Build WayFare MVP Backend executable"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the built executable"
    )
    args = parser.parse_args()
    
    print_section("WayFare MVP Backend Build Script")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check models
    has_models = check_models()
    
    # Clean if requested
    if args.clean:
        clean_build()
    
    # Run PyInstaller
    if not run_pyinstaller():
        print_summary(False, has_models)
        sys.exit(1)
    
    # Check output
    if not check_output():
        print_summary(False, has_models)
        sys.exit(1)
    
    # Test if requested
    if args.test:
        test_success = test_executable()
        if not test_success:
            print("\n⚠ Warning: Executable test failed")
    
    # Print summary
    print_summary(True, has_models)


if __name__ == "__main__":
    main()
