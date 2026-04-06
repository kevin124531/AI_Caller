from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from store.database import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_call_id: Mapped[str | None] = mapped_column(String(128), index=True)
    call_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    to_number: Mapped[str] = mapped_column(String(32))
    from_number: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str | None] = mapped_column(String(32))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    recording_url: Mapped[str | None] = mapped_column(Text)

    transcript: Mapped["Transcript | None"] = relationship(back_populates="call", uselist=False)
    scores: Mapped[list["Score"]] = relationship(back_populates="call")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[str] = mapped_column(String(128), ForeignKey("calls.call_id"), unique=True)
    s3_key: Mapped[str | None] = mapped_column(Text)
    exported_for_training: Mapped[bool] = mapped_column(default=False)

    call: Mapped["Call"] = relationship(back_populates="transcript")
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="transcript", order_by="TranscriptSegment.start_ms"
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcript_id: Mapped[int] = mapped_column(Integer, ForeignKey("transcripts.id"))
    role: Mapped[str] = mapped_column(String(16))   # "agent" | "user"
    content: Mapped[str] = mapped_column(Text)
    start_ms: Mapped[int | None] = mapped_column(Integer)
    end_ms: Mapped[int | None] = mapped_column(Integer)

    transcript: Mapped["Transcript"] = relationship(back_populates="segments")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[str] = mapped_column(String(128), ForeignKey("calls.call_id"))
    dimension: Mapped[str] = mapped_column(String(64))   # e.g. "sentiment", "completion_rate"
    value: Mapped[float] = mapped_column(Float)
    scorer_version: Mapped[str] = mapped_column(String(32), default="v1")

    call: Mapped["Call"] = relationship(back_populates="scores")
