from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Define the VOLI class
class VOLI(Base):
    __tablename__ = "VOLI"
    __table_args__ = {"schema": "ETL"}

    id_volo = Column(Integer, primary_key=True, autoincrement=True)
    data_ora_decollo = Column(String, nullable=False)
    data_ora_atterraggio = Column(String, nullable=False)
    marché = Column(String(length=7), ForeignKey("ANA.ANAAERO.MARCHE"), nullable=False)

    # Define the relationship with the ANAAERO table
    anaaero = relationship("ANAAERO")
