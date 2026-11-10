
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    Text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # SHA-256 fingerprint used to identify duplicate datasets
    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        index=True
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    column_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded"
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    records: Mapped[list["SalesRecord"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan"
    )


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    row_id: Mapped[int | None] = mapped_column(Integer)

    order_id: Mapped[str | None] = mapped_column(String(50))
    order_date: Mapped[datetime | None] = mapped_column(Date)
    ship_date: Mapped[datetime | None] = mapped_column(Date)
    ship_mode: Mapped[str | None] = mapped_column(String(100))

    customer_id: Mapped[str | None] = mapped_column(String(50))
    customer_name: Mapped[str | None] = mapped_column(String(150))
    segment: Mapped[str | None] = mapped_column(String(100))

    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(150))
    state: Mapped[str | None] = mapped_column(String(150))
    postal_code: Mapped[str | None] = mapped_column(String(30))
    region: Mapped[str | None] = mapped_column(String(100))

    product_id: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    sub_category: Mapped[str | None] = mapped_column(String(100))
    product_name: Mapped[str | None] = mapped_column(Text)

    sales: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    quantity: Mapped[int | None] = mapped_column(Integer)
    discount: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    profit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    dataset: Mapped["Dataset"] = relationship(
        back_populates="records"
    )
