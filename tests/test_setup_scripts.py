"""
Tests for setup scripts validation

This module tests that the setup scripts are properly formatted and contain
the required functionality.
"""

import os
import re
from pathlib import Path


def test_setup_sh_exists():
    """Test that setup.sh exists in the root directory"""
    setup_sh = Path("setup.sh")
    assert setup_sh.exists(), "setup.sh not found in root directory"


def test_setup_bat_exists():
    """Test that setup.bat exists in the root directory"""
    setup_bat = Path("setup.bat")
    assert setup_bat.exists(), "setup.bat not found in root directory"


def test_setup_sh_has_shebang():
    """Test that setup.sh has proper shebang"""
    with open("setup.sh", "r") as f:
        first_line = f.readline()
    assert first_line.startswith("#!/bin/bash"), "setup.sh missing proper shebang"


def test_setup_sh_has_required_steps():
    """Test that setup.sh contains all required setup steps"""
    with open("setup.sh", "r") as f:
        content = f.read()
    
    required_steps = [
        "python3",  # Python check
        "venv",  # Virtual environment
        "requirements-dev.txt",  # Dependencies
        "wayfare/models",  # Models directory
        "onnx",  # ONNX model
        "qdrant",  # Qdrant container
    ]
    
    for step in required_steps:
        assert step in content.lower(), f"setup.sh missing reference to: {step}"


def test_setup_bat_has_required_steps():
    """Test that setup.bat contains all required setup steps"""
    with open("setup.bat", "r") as f:
        content = f.read()
    
    required_steps = [
        "python",  # Python check
        "venv",  # Virtual environment
        "requirements-dev.txt",  # Dependencies
        "wayfare\\models",  # Models directory (Windows path)
        "onnx",  # ONNX model
        "qdrant",  # Qdrant container
    ]
    
    for step in required_steps:
        assert step in content.lower(), f"setup.bat missing reference to: {step}"


def test_setup_sh_has_error_handling():
    """Test that setup.sh has error handling"""
    with open("setup.sh", "r") as f:
        content = f.read()
    
    # Check for error handling patterns
    assert "set -e" in content or "exit" in content, "setup.sh missing error handling"


def test_setup_bat_has_error_handling():
    """Test that setup.bat has error handling"""
    with open("setup.bat", "r") as f:
        content = f.read()
    
    # Check for error handling patterns
    assert "errorlevel" in content.lower() or "exit" in content.lower(), \
        "setup.bat missing error handling"


def test_setup_sh_onnx_model_url():
    """Test that setup.sh has correct ONNX model URL"""
    with open("setup.sh", "r") as f:
        content = f.read()
    
    # Check for HuggingFace URL
    assert "huggingface.co" in content, "setup.sh missing HuggingFace URL"
    assert "bge-small-zh-v1.5" in content, "setup.sh missing correct model name"


def test_setup_bat_onnx_model_url():
    """Test that setup.bat has correct ONNX model URL"""
    with open("setup.bat", "r") as f:
        content = f.read()
    
    # Check for HuggingFace URL
    assert "huggingface.co" in content, "setup.bat missing HuggingFace URL"
    assert "bge-small-zh-v1.5" in content, "setup.bat missing correct model name"


def test_setup_sh_qdrant_port():
    """Test that setup.sh uses correct Qdrant port"""
    with open("setup.sh", "r") as f:
        content = f.read()
    
    assert "6333" in content, "setup.sh missing Qdrant port 6333"


def test_setup_bat_qdrant_port():
    """Test that setup.bat uses correct Qdrant port"""
    with open("setup.bat", "r") as f:
        content = f.read()
    
    assert "6333" in content, "setup.bat missing Qdrant port 6333"


def test_setup_sh_idempotent():
    """Test that setup.sh checks for existing resources"""
    with open("setup.sh", "r") as f:
        content = f.read()
    
    # Check for idempotency patterns
    idempotent_checks = [
        "already exists",
        "if [ -d",  # Directory check
        "if [ -f",  # File check
    ]
    
    found_checks = sum(1 for check in idempotent_checks if check in content)
    assert found_checks >= 2, "setup.sh may not be idempotent (missing existence checks)"


def test_setup_bat_idempotent():
    """Test that setup.bat checks for existing resources"""
    with open("setup.bat", "r") as f:
        content = f.read()
    
    # Check for idempotency patterns
    idempotent_checks = [
        "already exists",
        "if exist",  # Existence check
    ]
    
    found_checks = sum(1 for check in idempotent_checks if check.lower() in content.lower())
    assert found_checks >= 2, "setup.bat may not be idempotent (missing existence checks)"


def test_setup_guide_exists():
    """Test that SETUP_GUIDE.md exists"""
    setup_guide = Path("SETUP_GUIDE.md")
    assert setup_guide.exists(), "SETUP_GUIDE.md not found in root directory"


def test_setup_guide_has_sections():
    """Test that SETUP_GUIDE.md has required sections"""
    with open("SETUP_GUIDE.md", "r") as f:
        content = f.read()
    
    required_sections = [
        "Prerequisites",
        "Quick Start",
        "Linux/Mac",
        "Windows",
        "Troubleshooting",
    ]
    
    for section in required_sections:
        assert section in content, f"SETUP_GUIDE.md missing section: {section}"


def test_config_yaml_onnx_path():
    """Test that config.yaml has correct ONNX model path"""
    with open("config.yaml", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check that the path matches what setup scripts create
    assert "wayfare/models/bge-small-zh-v1.5.onnx" in content, \
        "config.yaml ONNX path doesn't match setup script output"


def test_setup_sh_docker_optional():
    """Test that setup.sh handles missing Docker gracefully"""
    with open("setup.sh", "r") as f:
        content = f.read()
    
    # Check for Docker availability check
    assert "docker" in content.lower(), "setup.sh doesn't check for Docker"
    assert "warning" in content.lower() or "skip" in content.lower(), \
        "setup.sh doesn't handle missing Docker gracefully"


def test_setup_bat_docker_optional():
    """Test that setup.bat handles missing Docker gracefully"""
    with open("setup.bat", "r") as f:
        content = f.read()
    
    # Check for Docker availability check
    assert "docker" in content.lower(), "setup.bat doesn't check for Docker"
    assert "warning" in content.lower() or "skip" in content.lower(), \
        "setup.bat doesn't handle missing Docker gracefully"
