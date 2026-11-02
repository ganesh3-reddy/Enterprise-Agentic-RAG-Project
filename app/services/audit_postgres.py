
import os
import psycopg


def write_postgres_audit(
    user_query: str,
    answer: str,
    source_used: str,
    status: str = "success",
    retries: int = 0
) -> int:
    """Write an audit record to PostgreSQL."""

    database_url = os.environ["DATABASE_URL"]

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    user_query,
                    answer,
                    source_used,
                    status,
                    retries
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_query,
                    answer,
                    source_used,
                    status,
                    retries
                )
            )

            record_id = cursor.fetchone()[0]

    return record_id
