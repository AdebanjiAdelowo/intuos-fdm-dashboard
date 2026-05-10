from sqlalchemy import Column, Integer, String, Float, DateTime, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ELMQTTMesTsage(Base):
    __tablename__ = "ETL_MQTT_MESSAGE"

    mqtt_message_id = Column(Integer, primary_key=True, autoincrement=True)
    datetime_message = Column(DateTime, server_default="now()")
    march = Column(String(7), nullable=False)
    mqtt_channel = Column(String(1), nullable=False)
    mqtt_subtopic = Column(String(1), nullable=False)
    payload_alfa = Column(String(150))
    payload_number = Column(Float)
    flag_z = Column(String(1), nullable=False)
    flag_gps = Column(String(1), nullable=False)
    alarm = Column(SmallInteger, nullable=False, server_default="0")
    alarm_type = Column(SmallInteger, nullable=False, server_default="0")
