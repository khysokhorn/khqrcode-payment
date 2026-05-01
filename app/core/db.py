from sqlmodel import create_engine, SQLModel, Session
import os

sqlite_file_name = "payment.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    from app.models.transaction import Transaction # Import models to register them
    from app.models.template import BankTemplate
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
