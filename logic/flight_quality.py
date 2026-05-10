from typing import Optional
import numpy as np
import scipy
import scipy.stats
from datamodels import TelemetrySample


class FlightQualityCalculator:
    def __init__(self, telemetry: list[TelemetrySample]) -> None:
        """
        Constructor for FlightQualityCalculator.

        This constructor takes a list of TelemetrySample objects and assigns the
        start and end indices of the takeoff and landing phases to the instance
        variables __takeoff_start, __takeoff_end, __landing_start, and
        __landing_end.

        :param telemetry: The list of telemetry samples.
        :type telemetry: list[TelemetrySample]
        """
        self.__complete_telemetry = telemetry
        self.__takeoff_start: Optional[int] = None
        self.__takeoff_end: Optional[int] = None
        self.__landing_start: Optional[int] = None
        self.__landing_end: Optional[int] = None

        for i, telemetry_sample in enumerate(telemetry):
            if (
                self.__takeoff_start is None
                and telemetry_sample.attitude == "landing-takeoff"
            ):
                self.__takeoff_start = i
                continue

            if (
                self.__takeoff_end is None
                and self.__takeoff_start is not None
                and telemetry_sample.attitude != "landing-takeoff"
            ):
                self.__takeoff_end = max(i, self.__takeoff_start + 10)
                continue

            if (
                self.__landing_start is None
                and self.__takeoff_start is not None
                and self.__takeoff_end is not None
                and telemetry_sample.attitude == "landing-takeoff"
            ):
                self.__landing_start = i
                continue

            if (
                self.__landing_end is None
                and self.__landing_start is not None
                and self.__takeoff_start is not None
                and self.__takeoff_end is not None
                and self.__landing_start is not None
                and telemetry_sample.attitude != "landing-takeoff"
            ):
                self.__landing_end = max(i, self.__landing_start + 10)
                break

    def get_flight_y_stats(self) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the y channel of the flight phase:
        - mean: the mean of the y channel
        - median: the median of the y channel
        - std: the standard deviation of the y channel
        - min: the minimum of the y channel
        - max: the maximum of the y channel

        :return: A dictionary containing the statistics of the y channel of the flight phase
        :rtype: dict[str, float]
        """
        flight_start = self.__takeoff_end
        flight_end = self.__landing_start
        return self.__get_y_stats(self.__complete_telemetry[flight_start:flight_end])

    def get_takeoff_y_stats(self) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the y channel of the takeoff phase:
        - mean: the mean of the y channel
        - median: the median of the y channel
        - std: the standard deviation of the y channel
        - min: the minimum of the y channel
        - max: the maximum of the y channel

        The start and end of the takeoff phase are determined by finding the first and last indices
        of the 'landing-takeoff' attitude in the telemetry list, and then offsetting them by 5 samples.

        :return: A dictionary containing the statistics of the y channel of the takeoff phase
        :rtype: dict[str, float]
        """
        takeoff_start, takeoff_end = self.__get_takeoff_range_with_offset(5)
        return self.__get_y_stats(self.__complete_telemetry[takeoff_start:takeoff_end])

    def get_landing_y_stats(self) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the y channel of the landing phase:
        - mean: the mean of the y channel
        - median: the median of the y channel
        - std: the standard deviation of the y channel
        - min: the minimum of the y channel
        - max: the maximum of the y channel

        The start and end of the landing phase are determined by finding the first and last indices
        of the 'landing-takeoff' attitude in the telemetry list, and then offsetting them by 5 samples.

        :return: A dictionary containing the statistics of the y channel of the landing phase
        :rtype: dict[str, float]
        """
        landing_start, landing_end = self.__get_landing_range_with_offset(5)
        return self.__get_y_stats(self.__complete_telemetry[landing_start:landing_end])

    def get_takeoff_z_stats(self) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the z channel of the takeoff phase:
        - mean: the mean of the z channel
        - median: the median of the z channel
        - std: the standard deviation of the z channel
        - min: the minimum of the z channel
        - max: the maximum of the z channel

        The start and end of the takeoff phase are determined by finding the first and last indices
        of the 'landing-takeoff' attitude in the telemetry list, and then offsetting them by 10 samples.

        :return: A dictionary containing the statistics of the z channel of the takeoff phase
        :rtype: dict[str, float]
        """
        takeoff_start, takeoff_end = self.__get_takeoff_range_with_offset(10)
        return self.__get_z_stats(self.__complete_telemetry[takeoff_start:takeoff_end])

    def get_landing_z_stats(self) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the z channel of the landing phase:
        - mean: the mean of the z channel
        - median: the median of the z channel
        - std: the standard deviation of the z channel
        - min: the minimum of the z channel
        - max: the maximum of the z channel

        The start and end of the landing phase are determined by finding the first and last indices
        of the 'landing-takeoff' attitude in the telemetry list, and then offsetting them by 10 samples.

        :return: A dictionary containing the statistics of the z channel of the landing phase
        :rtype: dict[str, float]
        """
        landing_start, landing_end = self.__get_landing_range_with_offset(10)
        return self.__get_z_stats(self.__complete_telemetry[landing_start:landing_end])

    def __get_takeoff_range_with_offset(self, offset):
        """
        Returns a tuple containing the start and end indices of the takeoff phase
        with the given offset applied.

        The start index is the maximum of the takeoff start index minus the offset
        and 0. The end index is the minimum of the takeoff end index plus the offset
        and the landing start index.

        The offset is useful for excluding the part of the takeoff phase that is
        close to the landing phase.

        :param offset: The offset to apply to the takeoff phase
        :type offset: int
        :return: A tuple containing the start and end indices of the takeoff phase
        :rtype: tuple[int, int]
        """
        return max(self.__takeoff_start - offset, 0), min(
            self.__takeoff_end + offset, self.__landing_start
        )

    def __get_landing_range_with_offset(self, offset):
        """
        Returns a tuple containing the start and end indices of the landing phase
        with the given offset applied.

        The start index is the maximum of the landing start index minus the offset
        and the takeoff end index. The end index is the minimum of the landing end
        index plus the offset and the length of the telemetry list.

        The offset is useful for excluding the part of the landing phase that is
        close to the takeoff phase.

        :param offset: The offset to apply to the landing phase
        :type offset: int
        :return: A tuple containing the start and end indices of the landing phase
        :rtype: tuple[int, int]
        """
        return max(self.__landing_start - offset, self.__takeoff_end), min(
            self.__landing_end + offset, len(self.__complete_telemetry)
        )

    def get_magnitutude_stats(self) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the magnitude of the acceleration
        of the flight:
        - mean: the mean of the magnitude of the acceleration
        - median: the median of the magnitude of the acceleration
        - std: the standard deviation of the magnitude of the acceleration
        - min: the minimum of the magnitude of the acceleration
        - max: the maximum of the magnitude of the acceleration

        The magnitude of the acceleration is calculated as the Euclidean norm of the acceleration vector.

        :return: A dictionary containing the statistics of the magnitude of the acceleration of the flight
        :rtype: dict[str, float]
        """
        g_tot = np.array(
            [
                telemetry_sample.g_tot
                for telemetry_sample in self.__complete_telemetry
                if telemetry_sample.g_tot is not None
            ]
        )
        return self.__get_stats(g_tot)

    def __get_x_stats(self, telemetry: list[TelemetrySample]) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the x component of the acceleration
        of the flight:
        - mean: the mean of the x component of the acceleration
        - median: the median of the x component of the acceleration
        - std: the standard deviation of the x component of the acceleration
        - min: the minimum of the x component of the acceleration
        - max: the maximum of the x component of the acceleration

        The x component of the acceleration is calculated as the x coordinate of the acceleration vector.

        :param telemetry: The telemetry data to calculate the statistics from
        :type telemetry: list[TelemetrySample]
        :return: A dictionary containing the statistics of the x component of the acceleration of the flight
        :rtype: dict[str, float]
        """
        acc_x = np.array(
            [
                telemetry_sample.acc_x
                for telemetry_sample in telemetry
                if telemetry_sample.acc_x is not None
            ]
        )
        return self.__get_stats(acc_x)

    def __get_y_stats(self, telemetry: list[TelemetrySample]) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the y component of the acceleration
        of the flight:
        - mean: the mean of the y component of the acceleration
        - median: the median of the y component of the acceleration
        - std: the standard deviation of the y component of the acceleration
        - min: the minimum of the y component of the acceleration
        - max: the maximum of the y component of the acceleration

        The y component of the acceleration is calculated as the y coordinate of the acceleration vector.

        :param telemetry: The telemetry data to calculate the statistics from
        :type telemetry: list[TelemetrySample]
        :return: A dictionary containing the statistics of the y component of the acceleration of the flight
        :rtype: dict[str, float]
        """
        acc_y = np.array(
            [
                telemetry_sample.acc_y
                for telemetry_sample in telemetry
                if telemetry_sample.acc_y is not None
            ]
        )
        return self.__get_stats(acc_y)

    def __get_z_stats(self, telemetry: list[TelemetrySample]) -> dict[str, float]:
        """
        Returns a dictionary containing the following statistics of the z component of the acceleration
        of the flight:
        - mean: the mean of the z component of the acceleration
        - median: the median of the z component of the acceleration
        - std: the standard deviation of the z component of the acceleration
        - min: the minimum of the z component of the acceleration
        - max: the maximum of the z component of the acceleration

        The z component of the acceleration is calculated as the z coordinate of the acceleration vector.

        :param telemetry: The telemetry data to calculate the statistics from
        :type telemetry: list[TelemetrySample]
        :return: A dictionary containing the statistics of the z component of the acceleration of the flight
        :rtype: dict[str, float]
        """
        acc_z = np.array(
            [
                telemetry_sample.acc_z
                for telemetry_sample in telemetry
                if telemetry_sample.acc_z is not None
            ]
        )
        return self.__get_stats(acc_z)

    @staticmethod
    def __get_stats(measurement: np.ndarray) -> dict[str, float]:
        """
        Calculate various statistics of a given measurement array.

        The statistics are:

        - nobs: the number of observations
        - min: the minimum value of the measurement
        - max: the maximum value of the measurement
        - mean: the mean of the measurement
        - std: the standard deviation of the measurement
        - variance: the variance of the measurement
        - skewness: the skewness of the measurement
        - kurtosis: the kurtosis of the measurement
        - energy: the energy of the measurement (sum of the squared differences from the mean)
        - mav: the mean absolute value of the measurement (mean of the absolute differences from the mean)
        - median: the median of the measurement
        - iqr: the interquartile range of the measurement
        - outliers_count: the number of outliers (values more than 2 standard deviations from the mean)
        - range: the range of the measurement (max - min)

        If the measurement array has less than 6 elements, the function returns a dictionary with all values set to 0.

        :param measurement: The measurement array
        :type measurement: np.ndarray
        :return: A dictionary containing the statistics of the measurement
        :rtype: dict[str, float]
        """
        if len(measurement) < 6:
            return {
                "nobs": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "std": 0,
                "variance": 0,
                "skewness": 0,
                "kurtosis": 0,
                "energy": 0,
                "mav": 0,
                "median": 0,
                "iqr": 0,
                "outliers_count": 0,
                "range": 0,
            }
        quality_index = scipy.stats.describe(measurement)
        z_score = scipy.stats.zscore(measurement)
        outliers = np.where(abs(z_score) > 2.0)
        outliers_count = len(outliers[0])

        return {
            "nobs": float(quality_index.nobs),
            "min": float(quality_index.minmax[0]),
            "max": float(quality_index.minmax[1]),
            "mean": float(quality_index.mean),
            "std": float(measurement.std()),
            "variance": float(quality_index.variance),
            "skewness": float(quality_index.skewness),
            "kurtosis": float(quality_index.kurtosis),
            "energy": float(np.sum(np.square(measurement - np.mean(measurement)))),
            "mav": float(np.mean(np.abs(measurement - np.mean(measurement)))),
            "median": float(np.median(measurement)),
            "iqr": float(
                np.percentile(measurement, 75) - np.percentile(measurement, 25)
            ),
            "outliers_count": float(outliers_count),
            "range": float(np.ptp(measurement)),
        }
