from sqlalchemy import create_engine, text
from src.config import config
import os
import logging

logger = logging.getLogger(__name__)

def init_db():
    """Initialize SQLite database with schema."""
    schema_path = "data/schema.sql"
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}")
        return

    engine = create_engine(f"sqlite:///{config.DB_PATH}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split SQL into individual statements
    statements = schema_sql.split(";")

    with engine.connect() as conn:
        for statement in statements:
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()
    
    logger.info(f"Database initialized at {config.DB_PATH}")

if __name__ == "__main__":
    init_db()
