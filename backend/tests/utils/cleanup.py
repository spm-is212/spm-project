"""
Generic test database cleanup utilities
"""
from typing import List, Dict, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD


class TestCleaner:
    """Generic utility for cleaning test tables completely"""

    def __init__(self):
        self.crud = SupabaseCRUD()

    def clear_table_completely(self, table_name: str) -> int:
        """
        Clear all records from a table completely
        Returns count of records deleted
        """
        try:
            # Use a filter that matches all records
            result = self.crud.delete(table_name, {"created_at": "neq.null"})
            return len(result) if isinstance(result, list) else 0
        except Exception as e:
            # Try alternative filters for different table structures
            try:
                result = self.crud.delete(table_name, {"id": "neq.null"})
                return len(result) if isinstance(result, list) else 0
            except Exception:
                try:
                    result = self.crud.delete(table_name, {"uuid": "neq.null"})
                    return len(result) if isinstance(result, list) else 0
                except Exception:
                    print(f"Warning: Could not clear table {table_name}: {e}")
                    return 0

    def clear_test_tables(self, table_names: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Clear all test tables (with _test suffix) completely
        Args:
            table_names: List of base table names (without _test suffix).
                        If None, uses default ['users', 'tasks']
        Returns count of records deleted per table
        """
        if table_names is None:
            table_names = ['users', 'tasks']

        cleared = {}

        for table in table_names:
            test_table = f"{table}_test"
            count = self.clear_table_completely(test_table)
            cleared[test_table] = count

        return cleared

    def clear_all_test_tables(self) -> Dict[str, int]:
        """
        Clear ALL test tables completely
        Convenience method for complete test cleanup
        """
        return self.clear_test_tables()

    def get_table_counts(self, table_names: List[str]) -> Dict[str, int]:
        """
        Get record counts for multiple tables
        """
        counts = {}
        for table in table_names:
            try:
                count = self.crud.count(table)
                counts[table] = count
            except Exception as e:
                counts[table] = f"Error: {e}"
        return counts


def clear_all_test_data(table_names: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Convenience function to clear all test tables
    Args:
        table_names: List of base table names. If None, uses ['users', 'tasks']
    Returns cleanup report
    """
    cleaner = TestCleaner()
    return cleaner.clear_test_tables(table_names)


def verify_test_tables_empty(table_names: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Verify test tables are empty
    Returns record counts for verification
    """
    if table_names is None:
        table_names = ['users', 'tasks']

    test_tables = [f"{table}_test" for table in table_names]
    cleaner = TestCleaner()
    return cleaner.get_table_counts(test_tables)


if __name__ == "__main__":
    print("🧹 Clearing all test tables...")
    report = clear_all_test_data()
    print(f"Cleared: {report}")

    print("\n🔍 Verifying tables are empty...")
    verification = verify_test_tables_empty()
    print(f"Current counts: {verification}")
