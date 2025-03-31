from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    links = relationship("Link", back_populates="owner")
    expired_links = relationship("ExpiredLink", back_populates="owner")

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, nullable=False, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    visit_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")

class ExpiredLink(Base):
    __tablename__ = "expired_links"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, nullable=False, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    visit_count = Column(Integer, default=0)
    expired_at = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="expired_links")

