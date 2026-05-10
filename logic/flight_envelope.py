from dataclasses import dataclass
import yaml
from datamodels import TelemetrySample


@dataclass
class GeneralFlightEnvelopeLimits:
    acceleration_safety_range: tuple[float]


@dataclass
class LowHeightFlightEnvelopeLimits:
    roll_min: float
    roll_max: float
    pitch_min: float
    pitch_max: float
    ground_speed_min: float
    acc_x_danger_range: tuple[float]


class FlightEnvelope:
    def __init__(self) -> None:
        """
        Initialize FlightEnvelope object.

        Loads limits from 'flight_envelope_limits.yaml' and assigns them to the
        corresponding class attributes.

        :return: None
        :rtype: None
        """
        with open("flight_envelope_limits.yaml") as f:
            limits = yaml.safe_load(f)
        self._general_limits = GeneralFlightEnvelopeLimits(
            **limits["general_envelope_limits"]
        )
        self._low_height_limits = LowHeightFlightEnvelopeLimits(
            **limits["low_height_envelope_limits"]
        )
        self._low_height_upper_limit = limits["low_height_upper_limit"]
        self._low_height_lower_limit = limits["low_height_lower_limit"]

    def get_general_limits(self) -> GeneralFlightEnvelopeLimits:
        """
        Return the general flight envelope limits.

        The general limits are the limits for all altitudes.

        :return: The general flight envelope limits
        :rtype: GeneralFlightEnvelopeLimits
        """
        return self._general_limits

    def get_low_height_limits(self) -> LowHeightFlightEnvelopeLimits:
        """
        Return the low height flight envelope limits.

        The low height limits are the limits when the airplane is below
        `low_height_upper_limit` and above `low_height_lower_limit` meters. 

        :return: The low height flight envelope limits
        :rtype: LowHeightFlightEnvelopeLimits
        """
        return self._low_height_limits

    def get_low_height_upper_limit(self) -> float:
        """
        Return the upper limit of the low height range in meters.

        The low height range is the range of altitudes where the airplane is
        below `low_height_upper_limit` and above `low_height_lower_limit` meters.

        :return: The upper limit of the low height range
        :rtype: float
        """
        return self._low_height_upper_limit

    def get_low_height_lower_limit(self) -> float:
        """
        Return the lower limit of the low height range in meters.

        The low height range is the range of altitudes where the airplane is
        below `low_height_upper_limit` and above `low_height_lower_limit` meters.

        :return: The lower limit of the low height range
        :rtype: float
        """
        return self._low_height_lower_limit


class FlightEnvelopeChecker:
    def __init__(self) -> None:
        """
        Initialize FlightEnvelopeChecker object.

        Loads limits from 'flight_envelope_limits.yaml' and assigns them to the
        corresponding class attributes.

        :return: None
        :rtype: None
        """
        flight_envelope = FlightEnvelope()
        self._general_limits = flight_envelope.get_general_limits()
        self._low_height_limits = flight_envelope.get_low_height_limits()
        self._low_height_upper_limit = flight_envelope.get_low_height_upper_limit()
        self._low_height_lower_limit = flight_envelope.get_low_height_lower_limit()

    def check(self, telemetry_item: TelemetrySample) -> TelemetrySample:
        """
        Check the given telemetry item for alarm conditions in the flight envelope.

        :param telemetry_item: The telemetry item to check
        :type telemetry_item: TelemetrySample
        :return: The telemetry item with alarms added if any conditions are met
        :rtype: TelemetrySample
        """
        if telemetry_item.height < self._low_height_upper_limit:
            # if telemetry_item.pitch < self._low_height_limits.pitch_min or telemetry_item.pitch > self._low_height_limits.pitch_max:
            #     telemetry_item.add_alarm('high pitch at low height')
            if (
                telemetry_item.roll < self._low_height_limits.roll_min
                or telemetry_item.roll > self._low_height_limits.roll_max
            ):
                telemetry_item.add_alarm("high_roll_at_low_height")
                
            if (
                telemetry_item.ground_speed < self._low_height_limits.ground_speed_min
            ) and self._low_height_limits.acc_x_danger_range[
                0
            ] < telemetry_item.acc_x < self._low_height_limits.acc_x_danger_range[
                1
            ]:
                telemetry_item.add_alarm(
                    "low_ground_speed_at_low_height_with_low_acceleration"
                )
            if (
                telemetry_item.pitch < self._low_height_limits.pitch_min
                or telemetry_item.pitch > self._low_height_limits.pitch_max
                and self._low_height_limits.acc_x_danger_range[0]
                < telemetry_item.acc_x
                < self._low_height_limits.acc_x_danger_range[1]
            ):
                telemetry_item.add_alarm(
                    "high_pitch_at_low_height_with_low_acceleration"
                )
        # if telemetry_item.height > self._low_height_upper_limit:
        #     if self._general_limits.acceleration_safety_range[0] > telemetry_item.acc_x > self._general_limits.acceleration_safety_range[1]:
        #         telemetry_item.add_alarm('Warning: high acceleration x')
        #     if self._general_limits.acceleration_safety_range[0] > telemetry_item.acc_y > self._general_limits.acceleration_safety_range[1]:
        #         telemetry_item.add_alarm('Warning: high acceleration y')
        #     if self._general_limits.acceleration_safety_range[0] > telemetry_item.acc_z > self._general_limits.acceleration_safety_range[1]:
        #         telemetry_item.add_alarm('Warning: high acceleration z')
        return telemetry_item
