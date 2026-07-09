from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class TicketStatus(str, Enum):
    open = "open"
    closed = "closed"


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus),
        default=TicketStatus.open,
        nullable=False,
        index=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    topic_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    topic_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user = relationship("User", back_populates="tickets")
    messages = relationship("Message", back_populates="ticket")
