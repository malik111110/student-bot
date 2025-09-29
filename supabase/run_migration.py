"""Run Supabase database migrations.

This script executes SQL migration files against the Supabase database.
It uses environment variables SUPABASE_URL and SUPABASE_KEY for authentication.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from supabase import create_client

# Load environment variables from .env file
load_dotenv()


def main():
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return 1

    # Initialize Supabase client
    client = create_client(url, key)

    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        return 1

    migration_file = sys.argv[1]
    migration_path = Path(__file__).parent / "migrations" / migration_file

    try:
        # Read migration SQL
        with open(migration_path, "r") as f:
            sql = f.read()

        # Execute migration
        print(f"Running migration: {migration_path.name}")

        if migration_file == "0000_create_exec_sql.sql":
            try:
                # Special case for creating exec_sql function
                result = client.functions.invoke(
                    "exec-sql", invoke_options={"body": {"sql_string": sql}}
                )
                print("Executed statement successfully")
            except Exception as stmt_error:
                print(f"Error executing statement: {str(stmt_error)}")
                return 1
        else:
            # Execute the entire SQL file as one statement to handle complex SQL properly
            try:
                result = client.postgrest.rpc("exec_sql", {"sql_string": sql}).execute()
                print(f"Executed migration successfully")
            except Exception as stmt_error:
                print(f"Error executing migration: {str(stmt_error)}")
                return 1

        print("Migration completed successfully")
        return 0

    except Exception as e:
        print(f"Error running migration: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
