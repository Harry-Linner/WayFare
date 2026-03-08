# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Build Specification for WayFare MVP Backend

This spec file configures PyInstaller to package the WayFare backend as a
standalone executable for use as a Tauri sidecar.

Key Features:
- Includes ONNX model files
- Includes configuration templates
- Configures hidden imports for packages PyInstaller might miss
- Creates a single-file executable for easy deployment

Usage:
    pyinstaller build.spec

Output:
    dist/wayfare-backend (or wayfare-backend.exe on Windows)
"""

import sys
from pathlib import Path

block_cipher = None

# Determine platform-specific settings
if sys.platform == 'win32':
    exe_name = 'wayfare-backend.exe'
elif sys.platform == 'darwin':
    exe_name = 'wayfare-backend'
else:  # Linux and other Unix-like systems
    exe_name = 'wayfare-backend'

a = Analysis(
    ['wayfare/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # ONNX model files (if they exist in wayfare/models/)
        ('wayfare/models/*.onnx', 'wayfare/models'),
        
        # Configuration template (if it exists)
        ('config.yaml', '.'),
        
        # README files for documentation
        ('wayfare/README*.md', 'wayfare'),
    ],
    hiddenimports=[
        # ONNX Runtime and dependencies
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi._pybind_state',
        
        # Qdrant client and dependencies
        'qdrant_client',
        'qdrant_client.http',
        'qdrant_client.http.models',
        'qdrant_client.conversions',
        
        # Transformers and tokenizers
        'transformers',
        'transformers.models',
        'transformers.models.bert',
        'tokenizers',
        
        # Database
        'aiosqlite',
        'sqlite3',
        
        # Pydantic
        'pydantic',
        'pydantic.dataclasses',
        'pydantic_settings',
        
        # Document parsing
        'fitz',  # PyMuPDF
        'markdown_it',
        'markdown_it.renderer',
        'markdown_it.parser_core',
        'markdown_it.parser_block',
        'markdown_it.parser_inline',
        
        # LiteLLM and LLM providers
        'litellm',
        'litellm.llms',
        'openai',
        'httpx',
        
        # Logging
        'loguru',
        
        # YAML
        'yaml',
        
        # Hashing
        'blake3',
        '_blake3',
        
        # Async support
        'asyncio',
        'concurrent.futures',
        
        # Numpy
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        
        # Typer (CLI framework)
        'typer',
        'click',
        
        # Standard library modules that might be missed
        'email',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        'html.parser',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'json',
        'pathlib',
        'argparse',
        'signal',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'hypothesis',
        'setuptools',
        'pip',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for IPC communication via stdin/stdout
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'path/to/icon.ico'
)
