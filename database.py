from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

DATABASE_URL = "sqlite:///./exylio.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"])

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True)
    email    = Column(String, unique=True)
    password = Column(String)
    name     = Column(String)

class Portfolio(Base):
    __tablename__ = "portfolio"
    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer)
    symbol    = Column(String)
    qty       = Column(Integer)
    avg_price = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    existing = db.query(User).filter_by(email="demo@exylio.com").first()
    if not existing:
        db.add(User(
            email="demo@exylio.com",
            password=pwd_context.hash("exylio123"),
            name="Demo Trader"
        ))
        db.commit()
    db.close()