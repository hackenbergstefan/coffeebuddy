from sqlalchemy import Column, Integer, String, LargeBinary
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tag = Column(LargeBinary)
    name = Column(String(50))
    prename = Column(String(50))
    coffees = Column(Integer)
