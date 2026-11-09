
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from .database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(100), nullable=False)
    speaker = Column(String(150), nullable=True)
    source_type = Column(String(50), default="text")
    language = Column(String(20), default="en-IN")
    transcript = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    assumptions = relationship(
        "Assumption",
        back_populates="source",
        cascade="all, delete-orphan"
    )


class Assumption(Base):
    __tablename__ = "assumptions"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(
        Integer,
        ForeignKey("sources.id"),
        nullable=True
    )

    department = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=False)
    metric = Column(String(150), nullable=False)
    value = Column(String(200), nullable=False)
    unit = Column(String(50), nullable=True)
    period = Column(String(100), nullable=True)

    assumption_type = Column(String(50), default="forecast")
    owner = Column(String(150), nullable=True)

    extraction_confidence = Column(Float, default=0.5)
    speaker_confidence = Column(Float, nullable=True)

    evidence = Column(Text, nullable=False)
    review_status = Column(String(30), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship(
        "Source",
        back_populates="assumptions"
    )


class Dependency(Base):
    __tablename__ = "dependencies"

    id = Column(Integer, primary_key=True, index=True)

    from_assumption_id = Column(
        Integer,
        ForeignKey("assumptions.id"),
        nullable=False
    )

    to_assumption_id = Column(
        Integer,
        ForeignKey("assumptions.id"),
        nullable=False
    )

    relation = Column(String(50), default="DEPENDS_ON")
    rationale = Column(Text, nullable=True)


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    finding_type = Column(String(50), nullable=False)
    severity = Column(String(30), default="medium")
    explanation = Column(Text, nullable=False)
    assumption_ids = Column(String(500), nullable=True)
    status = Column(String(30), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)

    changed_assumption_id = Column(
        Integer,
        ForeignKey("assumptions.id"),
        nullable=False
    )

    old_value = Column(String(200), nullable=True)
    new_value = Column(String(200), nullable=False)
    impact_summary = Column(Text, nullable=True)
    affected_assumption_ids = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
