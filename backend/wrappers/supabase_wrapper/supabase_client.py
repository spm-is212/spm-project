import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """
    Singleton Supabase client for database connections
    """
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._client = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
        return cls._instance

    @property
    def client(self):
        """Get the Supabase client instance"""
        return self._client

    def get_table(self, table_name: str):
        """Get a table reference for operations"""
        return self._client.table(table_name)
