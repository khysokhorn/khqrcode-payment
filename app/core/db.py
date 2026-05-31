from sqlmodel import create_engine, SQLModel, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///payment.db")

# For PostgreSQL, we might need to handle the 'postgres://' vs 'postgresql://' scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)

import time
from sqlalchemy.exc import OperationalError


def create_db_and_tables():
    from app.models.transaction import Transaction  # Import models to register them

    # Simple retry logic for Docker
    max_retries = 5
    for i in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("Successfully connected to the database!")
            break
        except OperationalError as e:
            if i == max_retries - 1:
                print(f"Failed to connect to database after {max_retries} attempts.")
                raise e
            print(f"Database not ready yet (attempt {i+1}/{max_retries}). Waiting...")
            time.sleep(2)


def get_session():
    with Session(engine) as session:
        yield session
