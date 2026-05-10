from math import sqrt
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from db_connection_params_handler import ConnectionParamsHandler


@dataclass
class AirplaneDatasheet:
    id: int
    registration_name: str
    country: str
    typedesignator: str

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "registration_name": self.registration_name,
            "country": self.country,
            "typedesignator": self.typedesignator,
        }

@dataclass
class PilotDatasheet:
    id: int
    pilot_name: str
    nationality: str
    instructor: str
    student: str

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "pilot_name": self.pilot_name,
            "nationality": self.nationality,
            "instructor": self.instructor,
            "student": self.student
        }

@dataclass
class Alarm:
    id: int
    registration_id: str
    vcc_min: float
    vcc_max: float
    icc_min: float
    icc_max: float
    temperature_box_min: float
    temperature_box_max: float
    g_tot_min: float
    g_tot_max: float
    ground_speed_max: float
    vertical_speed_max: float
    pitch_max: float
    roll_max: float
    height_min: float
    altitude_max: float

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "registration_id": self.registration_id,
            "vcc_min": self.vcc_min,
            "vcc_max": self.vcc_max,
            "icc_min": self.icc_min,
            "icc_max": self.icc_max,
            "temperature_box_min": self.temperature_box_min,
            "temperature_box_max": self.temperature_box_max,
            "g_tot_min": self.g_tot_min,
            "g_tot_max": self.g_tot_max,
            "ground_speed_max": self.ground_speed_max,
            "vertical_speed_max": self.vertical_speed_max,
            "pitch_max": self.pitch_max,
            "roll_max": self.roll_max,
            "height_min": self.height_min,
            "altitude_max": self.altitude_max,
        }


@dataclass
class Flight:
    id: int
    stick_on: Optional[datetime]
    stick_off: Optional[datetime]
    registration_id: str
    airport_takeoff: Optional[str]
    airport_landing: Optional[str]

    def get_on_box_as_unix_time(self):
        r = 0
        try:
            r = int(self.stick_on.timestamp())
        except ValueError:
            print("Error in get_on_box_as_unix_time")
            print(self.stick_on)
            pass
        return r

    def get_off_box_as_unix_time(self):
        r = datetime.now().timestamp()
        try:
            r = int(self.stick_off.timestamp())
        except ValueError:
            print("Error in get_off_box_as_unix_time")
            print(self.stick_off)
            pass
        return r

    def as_dict(self):
        return {
            "id": self.id,
            "stick_on": self.stick_on.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "stick_off": self.stick_off.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "registration_id": self.registration_id,
            "airport_takeoff": self.airport_takeoff,
            "airport_landing": self.airport_landing,
        }


class TelemetrySample:
    def __init__(self):
        self.__id: Optional[int] = None
        self.__registration_id: Optional[str] = None
        self.__flight_id: Optional[int] = None
        self.__unix_timestamp: Optional[int] = None
        self.__date_time: Optional[datetime] = None
        self.__vcc: Optional[float] = None
        self.__icc: Optional[float] = None
        self.__temperature_box: Optional[float] = None
        self.__magnetic_heading: Optional[float] = None
        self.__acc_x: Optional[float] = None
        self.__acc_y: Optional[float] = None
        self.__acc_z: Optional[float] = None
        self.__pitch: Optional[float] = None
        self.__roll: Optional[float] = None
        self.__turn_rate: Optional[float] = None
        self.__latitude: Optional[float] = None
        self.__longitude: Optional[float] = None
        self.__altitude: Optional[float] = None
        self.__ground_speed: Optional[float] = None
        self.__heading: Optional[float] = None
        self.__pressure: Optional[float] = None
        self.__pressure_altitude: Optional[float] = None
        self.__vertical_speed: Optional[float] = None
        self.__height: Optional[float] = None
        self.__elevation: Optional[float] = None
        self.__attitude: Optional[str] = None
        self.__alarms: Optional[list[str]] = None

    @property
    def id(self) -> Optional[int]:
        return self.__id

    @id.setter
    def id(self, value: int) -> None:
        self.__id = value

    @property
    def registration_id(self) -> Optional[str]:
        return self.__registration_id

    @registration_id.setter
    def registration_id(self, value: str) -> None:
        self.__registration_id = value

    @property
    def flight_id(self) -> Optional[int]:
        return self.__flight_id

    @flight_id.setter
    def flight_id(self, value: int) -> None:
        self.__flight_id = value

    @property
    def unix_timestamp(self) -> Optional[int]:
        return self.__unix_timestamp

    @unix_timestamp.setter
    def unix_timestamp(self, value: int) -> None:
        self.__unix_timestamp = value

    @property
    def date_time(self) -> Optional[datetime]:
        return self.__date_time

    @date_time.setter
    def date_time(self, value: datetime) -> None:
        self.__date_time = value

    @property
    def vcc(self) -> Optional[float]:
        return self.__vcc

    @vcc.setter
    def vcc(self, value: float) -> None:
        if abs(value) < 360:
            self.__vcc = value

    @property
    def icc(self) -> Optional[float]:
        return self.__icc

    @icc.setter
    def icc(self, value: float) -> None:
        if abs(value) < 360:
            self.__icc = value

    @property
    def temperature_box(self) -> Optional[float]:
        return self.__temperature_box

    @temperature_box.setter
    def temperature_box(self, value: float) -> None:
        if abs(value) < 360:
            self.__temperature_box = value

    @property
    def magnetic_heading(self) -> Optional[float]:
        return self.__magnetic_heading

    @magnetic_heading.setter
    def magnetic_heading(self, value: float) -> None:
        if abs(value) < 360:
            self.__magnetic_heading = value

    @property
    def acc_x(self) -> Optional[float]:
        return self.__acc_x

    @acc_x.setter
    def acc_x(self, value: float) -> None:
        if abs(value) < 9:
            self.__acc_x = value

    @property
    def acc_y(self) -> Optional[float]:
        return self.__acc_y

    @acc_y.setter
    def acc_y(self, value: float) -> None:
        if abs(value) < 9:
            self.__acc_y = value

    @property
    def acc_z(self) -> Optional[float]:
        return self.__acc_z

    @acc_z.setter
    def acc_z(self, value: float) -> None:
        if abs(value) < 9:
            self.__acc_z = value

    @property
    def pitch(self) -> Optional[float]:
        return -self.__pitch

    @pitch.setter
    def pitch(self, value: float) -> None:
        if abs(value) < 180:
            self.__pitch = value

    @property
    def roll(self) -> Optional[float]:
        return self.__roll

    @roll.setter
    def roll(self, value: float) -> None:
        if abs(value) < 180:
            self.__roll = value

    @property
    def turn_rate(self) -> Optional[float]:
        return self.__turn_rate

    @turn_rate.setter
    def turn_rate(self, value: float) -> None:
        if abs(value) < 180:
            self.__turn_rate = value

    @property
    def latitude(self) -> Optional[float]:
        return self.__latitude

    @latitude.setter
    def latitude(self, value: float) -> None:
        if abs(value) < 90:
            self.__latitude = value

    @property
    def longitude(self) -> Optional[float]:
        return self.__longitude

    @longitude.setter
    def longitude(self, value: float) -> None:
        if abs(value) < 180:
            self.__longitude = value

    @property
    def altitude(self) -> Optional[float]:
        return self.__altitude

    @altitude.setter
    def altitude(self, value: float) -> None:
        if value < 100_000:
            self.__altitude = value

    @property
    def ground_speed(self) -> Optional[float]:
        return self.__ground_speed

    @ground_speed.setter
    def ground_speed(self, value: float) -> None:
        if value < 1000:
            self.__ground_speed = value

    @property
    def heading(self) -> Optional[float]:
        return self.__heading

    @heading.setter
    def heading(self, value: float) -> None:
        if abs(value) < 360:
            self.__heading = value

    @property
    def pressure(self) -> Optional[float]:
        return self.__pressure

    @pressure.setter
    def pressure(self, value: float) -> None:
        if value < 10000:
            self.__pressure = value

    @property
    def pressure_altitude(self) -> Optional[float]:
        return self.__pressure_altitude

    @pressure_altitude.setter
    def pressure_altitude(self, value: float) -> None:
        if value < 10000:
            self.__pressure_altitude = value

    @property
    def vertical_speed(self) -> Optional[float]:
        # conversion from ft/s to ft/min
        return self.__vertical_speed * 60

    @vertical_speed.setter
    def vertical_speed(self, value: float) -> None:
        if value < 10000:
            self.__vertical_speed = value

    @property
    def height(self) -> Optional[float]:
        return self.__height

    @height.setter
    def height(self, value: float) -> None:
        if value < 10000:
            self.__height = value

    @property
    def elevation(self) -> Optional[float]:
        return self.__elevation

    @elevation.setter
    def elevation(self, value: float) -> None:
        if value < 100000:
            self.__elevation = value

    @property
    def attitude(self) -> Optional[str]:
        return self.__attitude

    @attitude.setter
    def attitude(self, value: str) -> None:
        self.__attitude = value

    @property
    def g_tot(self) -> Optional[float]:
        return (
            float(sqrt(self.acc_x**2 + self.acc_y**2 + self.acc_z**2))
            if self.acc_x is not None
            and self.acc_y is not None
            and self.acc_z is not None
            else None
        )
        
    @property
    def alarms(self) -> Optional[list[str]]:
        return self.__alarms

    @alarms.setter
    def alarms(self, value: Optional[list[str]]) -> None:
        self.__alarms = value

    def add_alarm(self, alarm: str) -> None:
        if self.__alarms is None:
            self.__alarms = []
        self.__alarms.append(alarm)

    def remove_alarm(self, alarm: str) -> None:
        if self.__alarms is not None:
            self.__alarms.remove(alarm)

    def clear_alarms(self) -> None:
        self.__alarms = None

    def has_alarms(self) -> bool:
        # if type(self.__alarms) is list:
        #    return len(self.__alarms) > 0
        return self.__alarms is not None  

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "registration_id": self.registration_id,
            "flight_id": self.flight_id,
            "unix_timestamp": self.unix_timestamp,
            "date_time": self.date_time.strftime("%Y-%m-%d %H:%M:%S"),
            "vcc": self.vcc,
            "icc": self.icc,
            "temperature_box": self.temperature_box,
            "magnetic_heading": self.magnetic_heading,
            "acc_x": self.acc_x,
            "acc_y": self.acc_y,
            "acc_z": self.acc_z,
            "pitch": self.pitch,
            "roll": self.roll,
            "turn_rate": self.turn_rate,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "ground_speed": self.ground_speed,
            "heading": self.heading,
            "pressure": self.pressure,
            "pressure_altitude": self.pressure_altitude,
            "vertical_speed": self.vertical_speed,
            "height": self.height,
            "elevation": self.elevation,
            "attitude": self.attitude,
            "g_tot": self.g_tot,
            "alarms": self.__alarms,
        }


@dataclass
class AlarmCount:
    registration: str = ""
    registration_id: str = ""
    g_tot: int = 0
    ground_speed: int = 0
    vertical_speed: int = 0
    pitch: int = 0
    roll: int = 0
    height: int = 0
    altitude: int = 0

    def add_gtot(self) -> None:
        self.g_tot += 1

    def add_ground_speed(self) -> None:
        self.ground_speed += 1

    def add_vertical_speed(self) -> None:
        self.vertical_speed += 1

    def add_pitch(self) -> None:
        self.pitch += 1

    def add_roll(self) -> None:
        self.roll += 1

    def add_height(self) -> None:
        self.height += 1

    def add_altitude(self) -> None:
        self.altitude += 1

    def sub_gtot(self) -> None:
        self.g_tot -= 1

    def sub_ground_speed(self) -> None:
        self.ground_speed -= 1

    def sub_vertical_speed(self) -> None:
        self.vertical_speed -= 1

    def sub_pitch(self) -> None:
        self.pitch -= 1

    def sub_roll(self) -> None:
        self.roll -= 1

    def sub_height(self) -> None:
        self.height -= 1

    def sub_altitude(self) -> None:
        self.altitude -= 1

    def as_dict(self) -> dict:
        return {
            "registration": self.registration,
            "registration_id": self.registration_id,
            "g_tot": self.g_tot,
            "ground_speed": self.ground_speed,
            "vertical_speed": self.vertical_speed,
            "pitch": self.pitch,
            "roll": self.roll,
            "height": self.height,
            "altitude": self.altitude,
        }


@dataclass
class LoginInfo:
    user_mail: str = ""
    user_password: str = ""
    db_host: str = ""
    db_port: str = ""
    db_name: str = ""
    flag_master: int = 0
    codcf: str = ""

    def update_connection_params_handler(
        self, connection_params: ConnectionParamsHandler
    ) -> ConnectionParamsHandler:
        connection_params.ip_address = self.db_host
        connection_params.port = self.db_port
        connection_params.db_name = self.db_name
        return connection_params

    def as_dict(self) -> dict:
        return {
            "user_mail": self.user_mail,
            "user_password": self.user_password,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "flag_master": self.flag_master,
            "codcf": self.codcf,
        }


@dataclass
class UserInfo:
    codcf: str
    # ragsoc1: str = None
    # ragsoc2: str = None
    # tipocf: str = None
    # giuridica: str = None
    # natonazcf: str = None
    # natocf: str = None
    # datanasc: date = None
    # indir1: str = None
    # indir2: str = None
    # capcf: str = None
    # citcf: str = None
    # prcf: str = None
    # nazcf: str = None
    # cfcfsn: str = None
    # cfcf: str = None
    # picfsn: str = None
    # picf: str = None
    # sociosn: str = None
    # numsocio: str = None
    # pilotasn: str = None
    # istrusn: str = None
    studentsn: str = None
    email: str = None
    telefono1: str = None
    telefono2: str = None
    # note1: str = None
    # note2: str = None
    # fisosn: str = None
    # aprsn: str = None
    # prospectsn: str = None
    # obbligatosn: str = None
    # examsn: str = None
    # aec_itasn: str = None
    # prospect_cate: str = None
    # web_password: str = None
    # flag_atoweb: int = 0
    # flag_webunit: int = 0
    # flag_reservation: int = 0
    # flag_operator: int = 0
    # flag_master: int = 0
    # flag_cbta: int = 0

    def as_dict(self) -> dict:
        return {
            "codcf": self.codcf,
            # "ragsoc1": self.ragsoc1,
            # "ragsoc2": self.ragsoc2,
            # "tipocf": self.tipocf,
            # "giuridica": self.giuridica,
            # "natonazcf": self.natonazcf,
            # "natocf": self.natocf,
            # "datanasc": (
            #     self.datanasc.isoformat() if self.datanasc is not None else None
            # ),
            # "indir1": self.indir1,
            # "indir2": self.indir2,
            # "capcf": self.capcf,
            # "citcf": self.citcf,
            # "prcf": self.prcf,
            # "nazcf": self.nazcf,
            # "cfcfsn": self.cfcfsn,
            # "cfcf": self.cfcf,
            # "picfsn": self.picfsn,
            # "picf": self.picf,
            # "sociosn": self.sociosn,
            # "numsocio": self.numsocio,
            # "pilotasn": self.pilotasn,
            # "istrusn": self.istrusn,
            "studentsn": self.studentsn,
            "email": self.email,
            "telefono1": self.telefono1,
            "telefono2": self.telefono2,
            # "note1": self.note1,
            # "note2": self.note2,
            # "fisosn": self.fisosn,
            # "aprsn": self.aprsn,
            # "prospectsn": self.prospectsn,
            # "obbligatosn": self.obbligatosn,
            # "examsn": self.examsn,
            # "aec_itasn": self.aec_itasn,
            # "prospect_cate": self.prospect_cate,
            # "web_password": self.web_password,
            # "flag_atoweb": self.flag_atoweb,
            # "flag_webunit": self.flag_webunit,
            # "flag_reservation": self.flag_reservation,
            # "flag_operator": self.flag_operator,
            # "flag_master": self.flag_master,
            # "flag_cbta": self.flag_cbta,
        }
