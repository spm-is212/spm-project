from typing import List, Dict, Any, Optional
from .supabase_client import SupabaseClient


class SupabaseCRUD:
    """
    General-purpose CRUD operations for Supabase
    """

    def __init__(self):
        self.client = SupabaseClient().client

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Select data from a table with optional filters

        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of column: value filters
            limit: Maximum number of rows to return
            order_by: Column to order by
            ascending: Sort order (True for ASC, False for DESC)

        Returns:
            List of dictionaries containing the results
        """
        query = self.client.table(table).select(columns)

        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)

        if order_by:
            query = query.order(order_by, desc=not ascending)

        if limit:
            query = query.limit(limit)

        result = query.execute()
        return result.data

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single record into a table

        Args:
            table: Table name
            data: Dictionary of column: value pairs

        Returns:
            Dictionary containing the inserted record
        """
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else None

    def insert_many(self, table: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Insert multiple records into a table

        Args:
            table: Table name
            data: List of dictionaries containing records

        Returns:
            List of dictionaries containing the inserted records
        """
        result = self.client.table(table).insert(data).execute()
        return result.data

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Update records in a table

        Args:
            table: Table name
            data: Dictionary of column: value pairs to update
            filters: Dictionary of column: value filters to match records

        Returns:
            List of dictionaries containing the updated records
        """
        query = self.client.table(table).update(data)

        for column, value in filters.items():
            query = query.eq(column, value)

        result = query.execute()
        return result.data

    def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Delete records from a table

        Args:
            table: Table name
            filters: Dictionary of column: value filters to match records

        Returns:
            List of dictionaries containing the deleted records
        """
        query = self.client.table(table).delete()

        for column, value in filters.items():
            query = query.eq(column, value)

        result = query.execute()
        return result.data

    def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records in a table

        Args:
            table: Table name
            filters: Optional dictionary of column: value filters

        Returns:
            Number of matching records
        """
        query = self.client.table(table).select("*", count="exact")

        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)

        result = query.execute()
        return result.count

    def exists(self, table: str, filters: Dict[str, Any]) -> bool:
        """
        Check if a record exists

        Args:
            table: Table name
            filters: Dictionary of column: value filters

        Returns:
            True if record exists, False otherwise
        """
        return self.count(table, filters) > 0
