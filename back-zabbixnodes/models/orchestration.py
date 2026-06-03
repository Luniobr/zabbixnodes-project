from datetime import datetime, timezone

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class OrchestrationRun(Base):
    __tablename__ = "orchestration_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered_by: Mapped[int | None] = mapped_column(ForeignKey("hub_users.id"))
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column()

    results: Mapped[list["OrchestrationResult"]] = relationship(
        "OrchestrationResult", back_populates="run"
    )


class OrchestrationResult(Base):
    __tablename__ = "orchestration_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orchestration_runs.id"))
    instance_id: Mapped[int | None] = mapped_column(ForeignKey("instances.id"))
    instance_name: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(20))
    details: Mapped[dict | None] = mapped_column(JSONB)
    executed_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    run: Mapped["OrchestrationRun"] = relationship("OrchestrationRun", back_populates="results")
    instance: Mapped["Instance | None"] = relationship("Instance", back_populates="orchestration_results")  # type: ignore[name-defined]
