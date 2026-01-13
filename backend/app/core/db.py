import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from app.core.settings import get_settings

engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    stored_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str] = mapped_column(Text)
    meta_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="documents")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="done")
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    has_issues: Mapped[bool | None] = mapped_column(nullable=True)
    issue_counts_json: Mapped[str] = mapped_column(Text, default="{}")
    queue_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="analyses")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metrics_json: Mapped[str] = mapped_column(Text)
    scores_json: Mapped[str] = mapped_column(Text)
    delta_json: Mapped[str] = mapped_column(Text, default="{}")
    meta_json: Mapped[str] = mapped_column(Text, default="{}")
    agent_latency_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

async def init_db():
    global engine, SessionLocal
    settings = get_settings()

    # ensure data dir exists
    os.makedirs("./data/uploads", exist_ok=True)

    engine = create_async_engine(settings.db_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_session() -> AsyncSession:
    if SessionLocal is None:
        raise RuntimeError("DB not initialized")
    return SessionLocal()
