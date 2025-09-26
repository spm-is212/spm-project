#!/usr/bin/env python3
"""
Comprehensive test cleanup script
Run this after pytest to ensure clean state for future tests
"""

from backend.tests.utils.cleanup import clear_all_test_data, verify_test_tables_empty


def main():
    print("SPM Project Test Cleanup")
    print("=" * 40)

    # Clear all test tables
    print("\n1. Clearing test tables...")
    cleanup_report = clear_all_test_data()

    for table, count in cleanup_report.items():
        if count > 0:
            print(f"   [OK] Cleared {count} records from {table}")
        else:
            print(f"   [INFO] {table} was already empty")

    # Verify cleanup
    print("\n2. Verifying cleanup...")
    verification = verify_test_tables_empty()

    all_clean = True
    for table, count in verification.items():
        if isinstance(count, int) and count == 0:
            print(f"   [OK] {table}: {count} records")
        else:
            print(f"   [ERROR] {table}: {count} records")
            all_clean = False

    # Final status
    print("\n" + "=" * 40)
    if all_clean:
        print("All test tables are clean!")
        print("Ready for future test runs")
    else:
        print("WARNING: Some tables still have data")
        print("Consider manual cleanup if needed")

    return all_clean


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
