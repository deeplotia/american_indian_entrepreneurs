#!/usr/bin/env python3
"""
Setup script for American Indian Entrepreneurs project.

This script helps users quickly set up the development environment.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_uv_installed():
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up American Indian Entrepreneurs Project")
    print("=" * 50)
    
    # Check if uv is installed
    if not check_uv_installed():
        print("❌ uv is not installed. Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   or visit: https://docs.astral.sh/uv/getting-started/installation/")
        return 1
    
    print("✅ uv is installed")
    
    # Install dependencies
    if not run_command("uv sync", "Installing core dependencies"):
        return 1
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print("✅ Created output directory")
    
    # Run test suite
    if not run_command("uv run pytest -q", "Running test suite"):
        print("⚠️  Test suite failed, but you can still try running the main script")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Run the main script: python src/run.py")
    print("2. Check the output directory for results")
    print("3. For development: uv sync --extra dev")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
