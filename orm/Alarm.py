from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BoxAlarm(Base):
    __tablename__ = "BOX_ALARM"

    ID = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    MARCHE = Column(String(7), ForeignKey("ANAAERO.MARCHE"), nullable=False)
    VCC_MIN = Column(Float, nullable=False, default=0)
    VCC_MAX = Column(Float, nullable=False, default=0)
    ICC_MIN = Column(Float, nullable=False, default=0)
    ICC_MAX = Column(Float, nullable=False, default=0)
    TINT_MIN = Column(Float, nullable=False, default=0)
    TINT_MAX = Column(Float, nullable=False, default=0)
    GTOT_MIN = Column(Float, nullable=False, default=0)
    GTOT_MAX = Column(Float, nullable=False, default=0)
    IAS_MAX = Column(Float, nullable=False, default=0)
    VSI_MAX = Column(Float, nullable=False, default=0)
    PITCH_MAX = Column(Float, nullable=False, default=0)
    ROLL_MAX = Column(Float, nullable=False, default=0)
    HEIGHT_MIN = Column(Float, nullable=False, default=0)
    ALTITUDE_MAX = Column(Float, nullable=False, default=0)

    anaaero = relationship("AnaAero", backref="box_alarms")
