from sqlmodel import create_engine, SQLModel, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///payment.db")

# For PostgreSQL, we might need to handle the 'postgres://' vs 'postgresql://' scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    from app.models.transaction import Transaction # Import models to register them
    from app.models.template import BankTemplate
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
