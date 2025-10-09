#!/usr/bin/env python3
"""
Test script to verify Databricks connection and Delta table setup.
Usage: python scripts/test_connection.py
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_environment():
    """Test that environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = ["DATABRICKS_HOST", "DATABRICKS_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"  ❌ {var} is not set")
        else:
            # Mask token in output
            value = os.getenv(var)
            if var == "DATABRICKS_TOKEN":
                value = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
            print(f"  ✅ {var} = {value}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or export them in your shell.")
        return False
    
    print("✅ All required environment variables are set\n")
    return True


def test_databricks_connection():
    """Test connection to Databricks."""
    print("🔌 Testing Databricks connection...")
    
    try:
        from app.databricks_client import DatabricksClient
        
        client = DatabricksClient()
        workspaces = client.get_accessible_workspaces()
        
        print(f"✅ Successfully connected to Databricks")
        print(f"  Found {len(workspaces)} workspace(s):")
        for ws in workspaces:
            print(f"    - {ws['workspace_name']} ({ws['workspace_id']})")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Databricks: {e}\n")
        return False


def test_delta_table():
    """Test Delta table initialization."""
    print("📊 Testing Delta table setup...")
    
    try:
        from app.delta_manager import DeltaManager
        
        manager = DeltaManager()
        print(f"✅ Delta table initialized at {manager.table_path}")
        
        # Try to read the table
        apps = manager.get_approved_apps()
        print(f"  Current approved apps count: {len(apps)}")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Delta table: {e}")
        print("  Note: This might be expected if Spark is not available locally.")
        print("  The table will be created when you deploy to Databricks.\n")
        return False


def test_api_models():
    """Test that API models can be imported."""
    print("📦 Testing API models...")
    
    try:
        from app.models import (
            DatabricksApp, ApprovalRequest, RevokeRequest,
            Workspace, AppsResponse, ApprovalDetails
        )
        print("✅ All API models imported successfully\n")
        return True
    except Exception as e:
        print(f"❌ Failed to import API models: {e}\n")
        return False


def main():
    """Run all tests."""
    print("🧪 Workspace Guardian - Connection Test\n")
    print("=" * 60)
    print()
    
    tests = [
        ("Environment Variables", test_environment),
        ("API Models", test_api_models),
        ("Databricks Connection", test_databricks_connection),
        ("Delta Table", test_delta_table),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Unexpected error in {test_name}: {e}\n")
            results[test_name] = False
    
    print("=" * 60)
    print("\n📊 Test Summary:\n")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print("🎉 All tests passed! Your setup looks good.")
        print("\nYou can now start the application:")
        print("  Backend:  uvicorn app.main:app --reload")
        print("  Frontend: cd frontend && npm run dev")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        print("\nCommon issues:")
        print("  - Environment variables not set (check .env file)")
        print("  - Invalid Databricks token or URL")
        print("  - Network connectivity issues")
        print("  - Missing Python dependencies (run: pip install -r requirements.txt)")
    
    print()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()




