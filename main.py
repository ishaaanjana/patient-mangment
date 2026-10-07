from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session


DATABASE_URL = "sqlite:///./patients.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    disease = Column(String, nullable=False)
    city = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

def calculate_bmi_and_verdict(height: float, weight: float):
    bmi = round(weight / (height ** 2), 2)
    if bmi < 18.5:
        verdict = "underweight"
    elif bmi < 25.0:
        verdict = "normal"
    elif bmi < 30.0:
        verdict = "overweight"
    else:
        verdict = "obese"
    return bmi, verdict


class PatientCreate(BaseModel):
    patient_code: str = Field(..., example="P101")
    name: str
    phone: str = Field(..., example="9876543210")
    blood_group: str = Field(..., example="O+")
    disease: str = Field(..., example="Fever / Diabetes")
    city: str
    age: int = Field(..., gt=0, lt=120)
    gender: str
    height: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)


class PatientResponse(BaseModel):
    id: int
    patient_code: str
    name: str
    phone: str
    blood_group: str
    disease: str
    city: str
    age: int
    gender: str
    height: float
    weight: float
    bmi: float
    verdict: str

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Hospital Patient Database System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def serve_home():
    return FileResponse("index.html")

@app.post("/patients", response_model=PatientResponse, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(PatientModel).filter(PatientModel.patient_code == payload.patient_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Yeh Patient Code pehle se database me maujood hai!")

    bmi, verdict = calculate_bmi_and_verdict(payload.height, payload.weight)

    new_patient = PatientModel(
        patient_code=payload.patient_code,
        name=payload.name,
        phone=payload.phone,
        blood_group=payload.blood_group,
        disease=payload.disease,
        city=payload.city,
        age=payload.age,
        gender=payload.gender,
        height=payload.height,
        weight=payload.weight,
        bmi=bmi,
        verdict=verdict
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@app.get("/patients", response_model=List[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    return db.query(PatientModel).all()

@app.delete("/patients/{patient_code}")
def delete_patient(patient_code: str, db: Session = Depends(get_db)):
    patient = db.query(PatientModel).filter(PatientModel.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient nahi mila!")
    
    db.delete(patient)
    db.commit()
    return 

