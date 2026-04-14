from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime
from enum import Enum
from typing import Generator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Date, DateTime, Enum as SqlEnum, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = "sqlite:///./applications.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(120), index=True)
    role_title: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        SqlEnum(ApplicationStatus),
        default=ApplicationStatus.SAVED,
        index=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    salary_expectation: Mapped[Optional[int]
                               ] = mapped_column(Integer, nullable=True)
    application_date: Mapped[date] = mapped_column(
        Date, default=date.today, index=True)
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )


class ApplicationCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=120)
    role_title: str = Field(..., min_length=2, max_length=120)
    status: ApplicationStatus = ApplicationStatus.SAVED
    location: Optional[str] = Field(None, max_length=120)
    salary_expectation: Optional[int] = Field(None, ge=0)
    application_date: date = Field(default_factory=date.today)
    contact_email: Optional[EmailStr] = None
    notes: Optional[str] = Field(None, max_length=3000)


class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=120)
    role_title: Optional[str] = Field(None, min_length=2, max_length=120)
    status: Optional[ApplicationStatus] = None
    location: Optional[str] = Field(None, max_length=120)
    salary_expectation: Optional[int] = Field(None, ge=0)
    application_date: Optional[date] = None
    contact_email: Optional[EmailStr] = None
    notes: Optional[str] = Field(None, max_length=3000)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    role_title: str
    status: ApplicationStatus
    location: Optional[str]
    salary_expectation: Optional[int]
    application_date: date
    contact_email: Optional[EmailStr]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class StatsResponse(BaseModel):
    total: int
    saved: int
    applied: int
    interview: int
    offer: int
    rejected: int


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Job Application Tracker API",
    description="Track internship and job applications with FastAPI + SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_application_or_404(db: Session, application_id: int) -> JobApplication:
    application = db.get(JobApplication, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/applications", response_model=ApplicationResponse, status_code=201)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
) -> JobApplication:
    application = JobApplication(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    status: Optional[ApplicationStatus] = Query(default=None),
    company: Optional[str] = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
) -> list[JobApplication]:
    query = db.query(JobApplication)

    if status:
        query = query.filter(JobApplication.status == status)
    if company:
        query = query.filter(JobApplication.company_name.ilike(f"%{company}%"))

    return query.order_by(JobApplication.application_date.desc()).all()


@app.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> JobApplication:
    return get_application_or_404(db, application_id)


@app.put("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> JobApplication:
    application = get_application_or_404(db, application_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(application, field_name, value)

    db.commit()
    db.refresh(application)
    return application


@app.delete("/applications/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> None:
    application = get_application_or_404(db, application_id)
    db.delete(application)
    db.commit()
    return None


@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    applications = db.query(JobApplication).all()

    counters = {
        ApplicationStatus.SAVED: 0,
        ApplicationStatus.APPLIED: 0,
        ApplicationStatus.INTERVIEW: 0,
        ApplicationStatus.OFFER: 0,
        ApplicationStatus.REJECTED: 0,
    }

    for item in applications:
        counters[item.status] += 1

    return StatsResponse(
        total=len(applications),
        saved=counters[ApplicationStatus.SAVED],
        applied=counters[ApplicationStatus.APPLIED],
        interview=counters[ApplicationStatus.INTERVIEW],
        offer=counters[ApplicationStatus.OFFER],
        rejected=counters[ApplicationStatus.REJECTED],
    )
