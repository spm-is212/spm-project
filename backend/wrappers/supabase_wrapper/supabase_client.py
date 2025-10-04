import os
from supabase import create_client, ClientOptions
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

            # Create client with connection timeout settings for Windows
            cls._client = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY"),
                options=ClientOptions(
                    postgrest_client_timeout=30,
                    storage_client_timeout=30,
                )
            )
        return cls._instance

    @property
    def client(self):
        """
        Get the Supabase client instance

        Returns:
            _type_: Supabase client instance
        """
        return self._client

    def get_table(self, table_name: str):
        """
        Get a reference to a specific table

        Args:
            table_name (str): Name of the table

        Returns:
            _type_: Table reference
        """
        return self._client.table(table_name)
