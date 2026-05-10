from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Float,
    LargeBinary,
)
from sqlalchemy.ext.declarative import declarative_base

# Define the SQLAlchemy model
Base = declarative_base()


class AnaAero(Base):
    __tablename__ = "ANAAERO"
    MARCHE = Column(String(7), primary_key=True)
    COUNTRY = Column(String(2), nullable=False)
    TC_HOLDER = Column(String(6), nullable=False)
    TYPEDESIGNATOR = Column(String(7), nullable=False)
    ICAO_ID = Column(Integer, nullable=False)
    NUMSERIE = Column(String(30), nullable=False)
    ANNOCOSTR = Column(Integer, nullable=False)
    ANNOIMMA = Column(Integer, nullable=False)
    ULMSN = Column(String(1), nullable=False)
    EXPERIMENTALSN = Column(String(1), nullable=False)
    RGSN = Column(String(1), nullable=False)
    VPSN = Column(String(1), nullable=False)
    IFRSN = Column(String(1), nullable=False)
    BIMOSN = Column(String(1), nullable=False)
    CODTIPOFUEL = Column(String(5), nullable=False)
    CODOWNER = Column(String(10), nullable=False)
    P_DAL = Column(Date, nullable=False)
    ESERCENZASN = Column(String(1), nullable=False)
    CODESERCENTE = Column(String(10), nullable=False)
    E_DAL = Column(Date, nullable=False)
    DESC_MODELLO = Column(String(50))
    ORESTART = Column(Integer, nullable=False, server_default="0")
    MINUTISTART = Column(Integer, nullable=False)
    DATASTART = Column(Date)
    GGCURRENT = Column(Integer, nullable=False)
    MTOW = Column(Integer, nullable=False)
    NUM_SEAT = Column(Integer, nullable=False)
    PHOTO_AEREO = Column(LargeBinary(2097152), nullable=False)
    ARC_DATASCAD = Column(Date)
    LESR_SCAD = Column(Date)
    ASSI_SCAD = Column(Date)
    PDM_SCAD = Column(Date)
    NOTE = Column(String(1000))
    LANDING_TOT = Column(Integer, nullable=False, server_default="0")
    CICLI_TOT = Column(Integer, nullable=False, server_default="0")
    SOTTOCAMOSN = Column(String(1), nullable=False, server_default="N")
    CONSUMO_ORARIO = Column(Float, nullable=False, server_default="0")
    AUT_IMP = Column(Integer, nullable=False, server_default="0")
    TURBINESN = Column(String(1), nullable=False, server_default="N")
    ENGINE_TYPE = Column(Integer, nullable=False, server_default="-1")
    RATING_NEEDED = Column(String(5))
    MPSN = Column(String(1), nullable=False, server_default="N")
    HELISN = Column(String(1), nullable=False, server_default="N")
    FUEL_UOM = Column(Integer, nullable=False, server_default="N")
