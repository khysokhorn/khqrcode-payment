from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tran_id: str = Field(index=True, unique=True)
    md5: Optional[str] = Field(default=None, index=True)

    amount: float
    currency: str = "USD"
    status: str = "PENDING"

    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    raw_response: Optional[str] = None
    qr_code_path: Optional[str] = None

    expired_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
