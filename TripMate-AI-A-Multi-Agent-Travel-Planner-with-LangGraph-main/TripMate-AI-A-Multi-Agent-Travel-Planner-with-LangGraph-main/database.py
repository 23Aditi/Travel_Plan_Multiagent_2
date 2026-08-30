import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger("tripmate.database")

def get_checkpointer(database_url: str = None):
    """
    Attempts to initialize PostgreSQL checkpointer using psycopg.
    If database_url is missing, invalid, or unreachable, gracefully falls back
    to LangGraph's MemorySaver to prevent crashes and keep the service operational.
    """
    if not database_url or "localhost" in database_url and not database_url.startswith("postgresql://"):
        logger.warning("DATABASE_URL is not configured. Using in-memory checkpointer (MemorySaver).")
        return MemorySaver()

    formatted_url = database_url
    if "sslmode=" not in formatted_url:
        separator = "&" if "?" in formatted_url else "?"
        formatted_url = f"{formatted_url}{separator}sslmode=require"

    try:
        import psycopg
        from psycopg.rows import dict_row
        from langgraph.checkpoint.postgres import PostgresSaver

        # Test connection with a fast timeout (5s)
        conn = psycopg.connect(
            formatted_url,
            autocommit=True,
            row_factory=dict_row,
            connect_timeout=5
        )
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()
        logger.info("Successfully connected to PostgreSQL checkpointer.")
        return checkpointer
    except Exception as exc:
        logger.warning(
            f"Could not connect to PostgreSQL checkpointer ({exc}). Falling back to MemorySaver for uninterrupted service."
        )
        return MemorySaver()
