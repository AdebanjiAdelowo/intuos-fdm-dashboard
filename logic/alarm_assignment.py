from math import sqrt

import pandas as pd
from datamodels import Alarm, AlarmCount, TelemetrySample
from logic.flight_envelope import FlightEnvelopeChecker


def assign_alarms_single(telemetry_item, alarms):
    """
    Assign alarm conditions to a single telemetry item.

    The function takes a telemetry item as input (in dictionary form) and a dictionary of Alarm objects,
    keyed by registration_id. It assigns alarm conditions to the telemetry item by comparing its values
    to the limits in the Alarm object for its registration_id, and adds the alarm conditions to the
    telemetry item's "alarms" list. The modified telemetry item is returned.

    :param telemetry_item: The telemetry item to assign alarms to
    :type telemetry_item: dict
    :param alarms: A dictionary of Alarm objects, keyed by registration_id
    :type alarms: dict[str, Alarm]
    :return: The telemetry item with alarms added
    :rtype: dict
    """
    telemetry_item["g_tot"] = sqrt(
        telemetry_item["acc_x"] ** 2
        + telemetry_item["acc_y"] ** 2
        + telemetry_item["acc_z"] ** 2
    )
    telemetry_item["alarms"] = []
    telemetry_item["date_time"] = telemetry_item["date_time"].strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    if (
        not (alarms[telemetry_item["registration_id"]].g_tot_min
        < telemetry_item["g_tot"]
        < alarms[telemetry_item["registration_id"]].g_tot_max)
    ):
        telemetry_item["alarms"].append("g_tot")
    if (
        alarms[telemetry_item["registration_id"]].ground_speed_max
        < telemetry_item["ground_speed"] #<=?
    ):
        telemetry_item["alarms"].append("ground_speed")
    if (
         alarms[telemetry_item["registration_id"]].vertical_speed_max
        < telemetry_item["vertical_speed"] #<=?
    ):
        telemetry_item["alarms"].append("vertical_speed")
    if (
         abs(alarms[telemetry_item["registration_id"]].pitch_max)
        < telemetry_item["pitch"] #<=?
    ):
        telemetry_item["alarms"].append("pitch")
    if (
        abs(alarms[telemetry_item["registration_id"]].roll_max)
        < telemetry_item["roll"]
    ):
        telemetry_item["alarms"].append("roll")
    if (
         alarms[telemetry_item["registration_id"]].altitude_max
        < telemetry_item["altitude"]
    ):
        telemetry_item["alarms"].append("altitude")
    return telemetry_item


def assign_alarms_v2(flight_telemetry, alarms):
    """
    Assign alarm conditions to a list of telemetry samples.

    The function takes a DataFrame of telemetry samples and a dictionary of Alarm objects
    as input. It fills NaN values in the telemetry DataFrame with 0, converts the DataFrame
    to a list of dictionaries, and then assigns alarm conditions to each telemetry sample
    by calling the assign_alarms_single function. The results are returned as a list of
    dictionaries.

    :param flight_telemetry: The telemetry samples to assign alarms to
    :type flight_telemetry: pd.DataFrame
    :param alarms: A dictionary of Alarm objects, keyed by registration_id
    :type alarms: dict[str, Alarm]
    :return: A list of telemetry samples with alarms assigned
    :rtype: list[dict]
    """
    flight_telemetry_0 = flight_telemetry.fillna(0).infer_objects(copy=False)
    telemetry = flight_telemetry_0.to_dict(orient="records")
    results = [
        assign_alarms_single(telemetry_item, alarms) for telemetry_item in telemetry
    ]
    return results


def count_alarms(flight_telemetry: list[TelemetrySample]) -> list[AlarmCount]:
    """
    Count the number of times each alarm condition is triggered in the given list of telemetry samples.

    :param flight_telemetry: The telemetry samples to count alarms for
    :type flight_telemetry: list[TelemetrySample]
    :return: A dictionary mapping registration_id to AlarmCount objects
    :rtype: list[AlarmCount]
    """
    alarm_finder: dict = {}
    alarms: dict = {}
    for telemetry in flight_telemetry:
        if telemetry.registration_id not in alarms:
            alarms[telemetry.registration_id] = telemetry.registration.alarms[0]
        alarm = alarms[telemetry.registration_id]

        if telemetry.registration_id not in alarm_finder:
            alarm_finder[telemetry.registration_id] = AlarmCount(
                registration=telemetry.registration.registration_name,
                registration_id=telemetry.registration_id,
            )
        alarm_count = alarm_finder[telemetry.registration_id]

        alarm_count.g_tot += (
            telemetry.g_tot > alarm.g_tot_max or telemetry.g_tot < alarm.g_tot_min
        )
        alarm_count.ground_speed += alarm.ground_speed_max < telemetry.ground_speed
        alarm_count.vertical_speed += (
            alarm.vertical_speed_max < telemetry.vertical_speed
        )
        alarm_count.pitch += alarm.pitch_max < abs(telemetry.pitch)
        alarm_count.roll += alarm.roll_max < abs(telemetry.roll)
        alarm_count.altitude += alarm.altitude_max < telemetry.altitude

    return list(alarm_finder.values())


class AlarmHandler:
    def __init__(self, alarms: list[Alarm]):
        """
        Initialize AlarmHandler object.

        Store the given alarms in a dictionary for fast lookups and initialize
        an AlarmCount object for each registration_id.

        :param alarms: The alarms to store
        :type alarms: list[Alarm]
        """

        self.__alarms: dict[Alarm] = {alarm.registration_id: alarm for alarm in alarms}
        self.__alarm_counters: dict[AlarmCount] = {
            alarm.registration_id: AlarmCount(
                alarm.registration_id, alarm.registration_id
            )
            for alarm in alarms
        }
        self._previous_telemetry = None
        self._flight_envelope_checker = FlightEnvelopeChecker()

    def __calculate_average_telemetry(
        self, telemetry_item: TelemetrySample
    ) -> TelemetrySample:
        """
        Calculate the average of the telemetry item with the previously stored telemetry item.

        If the previous telemetry item is None, return the given telemetry item.
        If the ids of the two telemetry items are the same, return the given telemetry item.
        Otherwise, calculate the average of the two telemetry items and return it.
        """
        average_telemetry = TelemetrySample()

        if self._previous_telemetry is None:
            self._previous_telemetry = telemetry_item
            return telemetry_item

        if self._previous_telemetry.id == telemetry_item.id:
            return telemetry_item

        average_telemetry.vcc = (
            (self._previous_telemetry.vcc + telemetry_item.vcc) / 2
            if self._previous_telemetry.vcc is not None
            and telemetry_item.vcc is not None
            else 0
        )
        average_telemetry.icc = (
            (self._previous_telemetry.icc + telemetry_item.icc) / 2
            if self._previous_telemetry.icc is not None
            and telemetry_item.icc is not None
            else 0
        )
        average_telemetry.temperature_box = (
            (self._previous_telemetry.temperature_box + telemetry_item.temperature_box)
            / 2
            if self._previous_telemetry.temperature_box is not None
            and telemetry_item.temperature_box is not None
            else 0
        )
        average_telemetry.magnetic_heading = (
            (
                self._previous_telemetry.magnetic_heading
                + telemetry_item.magnetic_heading
            )
            / 2
            if self._previous_telemetry.magnetic_heading is not None
            and telemetry_item.magnetic_heading is not None
            else 0
        )
        average_telemetry.acc_x = (
            (self._previous_telemetry.acc_x + telemetry_item.acc_x) / 2
            if self._previous_telemetry.acc_x is not None
            and telemetry_item.acc_x is not None
            else 0
        )
        average_telemetry.acc_y = (
            (self._previous_telemetry.acc_y + telemetry_item.acc_y) / 2
            if self._previous_telemetry.acc_y is not None
            and telemetry_item.acc_y is not None
            else 0
        )
        average_telemetry.acc_z = (
            (self._previous_telemetry.acc_z + telemetry_item.acc_z) / 2
            if self._previous_telemetry.acc_z is not None
            and telemetry_item.acc_z is not None
            else 0
        )
        average_telemetry.pitch = (
            (self._previous_telemetry.pitch + telemetry_item.pitch) / 2
            if self._previous_telemetry.pitch is not None
            and telemetry_item.pitch is not None
            else 0
        )
        average_telemetry.roll = (
            (self._previous_telemetry.roll + telemetry_item.roll) / 2
            if self._previous_telemetry.roll is not None
            and telemetry_item.roll is not None
            else 0
        )
        average_telemetry.turn_rate = (
            (self._previous_telemetry.turn_rate + telemetry_item.turn_rate) / 2
            if self._previous_telemetry.turn_rate is not None
            and telemetry_item.turn_rate is not None
            else 0
        )
        average_telemetry.latitude = (
            (self._previous_telemetry.latitude + telemetry_item.latitude) / 2
            if self._previous_telemetry.latitude is not None
            and telemetry_item.latitude is not None
            else 0
        )
        average_telemetry.longitude = (
            (self._previous_telemetry.longitude + telemetry_item.longitude) / 2
            if self._previous_telemetry.longitude is not None
            and telemetry_item.longitude is not None
            else 0
        )
        average_telemetry.altitude = (
            (self._previous_telemetry.altitude + telemetry_item.altitude) / 2
            if self._previous_telemetry.altitude is not None
            and telemetry_item.altitude is not None
            else 0
        )
        average_telemetry.ground_speed = (
            (self._previous_telemetry.ground_speed + telemetry_item.ground_speed) / 2
            if self._previous_telemetry.ground_speed is not None
            and telemetry_item.ground_speed is not None
            else 0
        )
        average_telemetry.heading = (
            (self._previous_telemetry.heading + telemetry_item.heading) / 2
            if self._previous_telemetry.heading is not None
            and telemetry_item.heading is not None
            else 0
        )
        average_telemetry.pressure = (
            (self._previous_telemetry.pressure + telemetry_item.pressure) / 2
            if self._previous_telemetry.pressure is not None
            and telemetry_item.pressure is not None
            else 0
        )
        average_telemetry.pressure_altitude = (
            (
                self._previous_telemetry.pressure_altitude
                + telemetry_item.pressure_altitude
            )
            / 2
            if self._previous_telemetry.pressure_altitude is not None
            and telemetry_item.pressure_altitude is not None
            else 0
        )
        average_telemetry.vertical_speed = (
            (self._previous_telemetry.vertical_speed + telemetry_item.vertical_speed)
            / 2
            if self._previous_telemetry.vertical_speed is not None
            and telemetry_item.vertical_speed is not None
            else 0
        )
        average_telemetry.height = (
            (self._previous_telemetry.height + telemetry_item.height) / 2
            if self._previous_telemetry.height is not None
            and telemetry_item.height is not None
            else 0
        )

        return average_telemetry

    def assign_alarm_to_telemetry(
        self, telemetry_item: TelemetrySample
    ) -> TelemetrySample:
        # todo: comment following line for silveri algorithm
        # self._previous_telemetry = telemetry_item

        """
        Assign alarms to a telemetry item based on predefined limits in the Alarm objects.

        :param telemetry_item: The telemetry item to check
        :type telemetry_item: TelemetrySample
        :return: The telemetry item with alarms added if any conditions are met
        :rtype: TelemetrySample
        """
        alarms = self.__alarms
        reg_id = telemetry_item.registration_id

        if (
            telemetry_item.attitude == "taxing"
            or telemetry_item.attitude == "landing-takeoff"
        ):
            return telemetry_item

        # average_telemetry = self.__calculate_average_telemetry(telemetry_item)
        if reg_id not in alarms:
            return telemetry_item
        if (
            not alarms[reg_id].g_tot_min
            < telemetry_item.g_tot
            < alarms[reg_id].g_tot_max
        ):
            telemetry_item.add_alarm("g_tot")
            self.__alarm_counters[reg_id].add_gtot()
        if not alarms[reg_id].ground_speed_max > telemetry_item.ground_speed:
            telemetry_item.add_alarm("ground_speed")
            self.__alarm_counters[reg_id].add_ground_speed()
        if not alarms[reg_id].vertical_speed_max > telemetry_item.vertical_speed:
            telemetry_item.add_alarm("vertical_speed")
            self.__alarm_counters[reg_id].add_vertical_speed()
        if not alarms[reg_id].pitch_max > abs(telemetry_item.pitch):
            telemetry_item.add_alarm("pitch")
            self.__alarm_counters[reg_id].add_pitch()
        if not alarms[reg_id].roll_max > abs(telemetry_item.roll):
            telemetry_item.add_alarm("roll")
            self.__alarm_counters[reg_id].add_roll()
        # if  ((alarms[reg_id].height_min > average_telemetry.height) and (telemetry_item.ground_speed > 75)):
        #     telemetry_item.add_alarm('height')
        #     self.__alarm_counters[reg_id].add_height()
        if not alarms[reg_id].altitude_max > telemetry_item.altitude:
            telemetry_item.add_alarm("altitude")
            self.__alarm_counters[reg_id].add_altitude()

        telemetry_item = self._flight_envelope_checker.check(telemetry_item)
        self._previous_telemetry = telemetry_item
        return telemetry_item

    def get_alarm_counters(self) -> list[AlarmCount]:
        """
        Return a list of AlarmCount objects, one for each registration_id in the alarms dict.

        :return: A list of AlarmCount objects
        :rtype: list[AlarmCount]
        """
        return list(self.__alarm_counters.values())


class AlarmHandlerDF:
    def __init__(self, alarms: list[Alarm]):
        """
        Initialize AlarmHandlerDF object.

        Store the given alarms in a dictionary for fast lookups and initialize
        an AlarmCount object for each registration_id.

        :param alarms: The alarms to store
        :type alarms: list[Alarm]
        """
        self.__alarms: dict[Alarm] = {alarm.registration_id: alarm for alarm in alarms}
        self.__alarm_counters: dict[AlarmCount] = {
            alarm.registration_id: AlarmCount(
                alarm.registration_id, alarm.registration_id
            )
            for alarm in alarms
        }

    def assign_alarm_to_telemetry(self, telemetry: pd.DataFrame) -> pd.DataFrame:
        alarms = self.__alarms
        alarms_triggered: pd.DataFrame = pd.DataFrame(
            columns=[
                "unix_timestamp",
                "vcc",
                "icc",
                "g_tot",
                "ground_speed",
                "vertical_speed",
                "pitch",
                "roll",
                "height",
                "altitude",
            ]
        )

        alarms_triggered["unix_timestamp"] = telemetry["unix_timestamp"]
        alarms_triggered["vcc"] = telemetry.apply(
            lambda x: (
                True
                if x.vcc > alarms[x.registration_id].vcc_max
                or x.vcc < alarms[x.registration_id].vcc_min
                else False
            ),
            axis=1,
        )
        alarms_triggered["icc"] = telemetry.apply(
            lambda x: (
                True
                if x.icc > alarms[x.registration_id].icc_max
                or x.icc < alarms[x.registration_id].icc_min
                else False
            ),
            axis=1,
        )
        alarms_triggered["g_tot"] = telemetry.apply(
            lambda x: (
                True
                if x.g_tot > alarms[x.registration_id].g_tot_max
                or x.g_tot < alarms[x.registration_id].g_tot_min
                else False
            ),
            axis=1,
        )
        alarms_triggered["ground_speed"] = telemetry.apply(
            lambda x: (
                True
                if alarms[x.registration_id].ground_speed_max < x.ground_speed
                else False
            ),
            axis=1,
        )
        alarms_triggered["vertical_speed"] = telemetry.apply(
            lambda x: (
                True
                if alarms[x.registration_id].vertical_speed_max < x.vertical_speed
                else False
            ),
            axis=1,
        )
        alarms_triggered["pitch"] = telemetry.apply(
            lambda x: (
                True if alarms[x.registration_id].pitch_max < abs(x.pitch) else False
            ),
            axis=1,
        )
        alarms_triggered["roll"] = telemetry.apply(
            lambda x: (
                True if alarms[x.registration_id].roll_max < abs(x.roll) else False
            ),
            axis=1,
        )
        alarms_triggered["height"] = telemetry.apply(
            lambda x: (
                True if x.height > alarms[x.registration_id].height_min else False
            ),
            axis=1,
        )
        alarms_triggered["altitude"] = telemetry.apply(
            lambda x: (
                True if alarms[x.registration_id].altitude_max < x.altitude else False
            ),
            axis=1,
        )

        return alarms_triggered
