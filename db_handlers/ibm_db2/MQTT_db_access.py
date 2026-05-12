from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from logic.flight_envelope import FlightEnvelope


class TelemetryMQTTDatabaseAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        """
        Constructor for TelemetryMQTTDatabaseAccess.

        :param manager: A DatabaseManager object, used to query the database.
        :type manager: DatabaseManager
        :return: No return value
        :rtype: None
        """
        self.__manager = manager
        self.flight_envelope = FlightEnvelope()

    def get_telemetry_by_datetime_interval_unformatted(
        self, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given datetime interval.

        The data is not formatted in any way, and is returned as is from the database.

        Parameters
        ----------
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = """SELECT * FROM ETL.ETL_MQTT_MESSAGE
                    WHERE DATETIME_MESSAGE >= ? AND DATETIME_MESSAGE <= ?
                    AND MQTT_CHANNEL IN ('N', 'E') AND MQTT_SUBTOPIC IN ('0', '1', '2','5', '6','7','9', 'V', '-')
                """
        return self.__manager.get_query_result(query, [start_datetime, end_datetime])

    def get_telemetry_by_marca_datetime_interval_unformatted(
        self, marca: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is not formatted in any way, and is returned as is from the database.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = """SELECT * FROM ETL.ETL_MQTT_MESSAGE WHERE MARCHE = ?
                        AND DATETIME_MESSAGE >= ? AND DATETIME_MESSAGE <= ?
                        AND MQTT_CHANNEL IN ('N', 'E') AND MQTT_SUBTOPIC IN ('0', '1', '2','5', '6','7','9', 'V', '-')
                """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])

    def get_telemetry_by_marca_unformatted(self, marca: str):
        """
        Retrieves all telemetry data from the database for the given marca.

        The data is not formatted in any way, and is returned as is from the database.

        Parameters
        ----------
        marca : str
            The marca to filter by.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = """SELECT * FROM ETL.ETL_MQTT_MESSAGE WHERE MARCHE = ?
                        AND MQTT_CHANNEL IN ('N', 'E') AND MQTT_SUBTOPIC IN ('0', '1', '2','5', '6','7','9', 'V', '-')
                """
        return self.__manager.get_query_result(query, [marca])
    
    def get_telemetry_by_marcas_datetime_interval(
        self, marcas: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marcas : list[str]
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        marcas = list(marcas)
        placeholders = ", ".join("?" for _ in marcas)
        query = f"""
            WITH base_data AS (
                SELECT
                    msg.MARCHE,  -- Include the MARCHE column here for filtering
                    msg.datetime_message,
                    msg.mqtt_channel,
                    msg.mqtt_subtopic,
                    msg.payload_alfa
                FROM
                    etl.etl_mqtt_message msg
                JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                WHERE
                    msg.MARCHE IN ({placeholders})
                    AND msg.flag_gps = '1'
                    AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                    AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2')
                    AND msg.mqtt_channel = 'N'
                    AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                    ),
           grouped_7 AS (
                SELECT
                    marche,
                    datetime_message AS date_time,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                FROM
                    base_data  
                GROUP BY marche, datetime_message 
            ), 
            final1 AS (
                SELECT
                    g7.marche,
                    g7.date_time,
                    g7.gps_payload,
                    g7.ahrs_payload, 
                    g7.vcc,
                    g7.icc,
                    REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                    SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                    SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                    SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                    SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                    SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                    SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                    g7.vertical_speed,
                    g7.magnetic_heading,
                    e.payload_alfa AS elevation
                FROM grouped_7 g7
                    LEFT JOIN LATERAL (
                        SELECT e1.payload_alfa
                        FROM etl.etl_mqtt_message e1
                        WHERE e1.marche = g7.marche
                            AND e1.mqtt_channel = 'E'
                            AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                            AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                        ORDER BY e1.datetime_message DESC
                        FETCH FIRST 1 ROW ONLY
                    ) AS e ON 1=1
            ),
            final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND 
                            f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND 
                            f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f
                JOIN
                    base.box_alarm b
                    ON f.marche = b.marche
        """
        return self.__manager.get_query_result(query, marcas + [start_datetime, end_datetime])

    def get_telemetry_by_flight(
        self, id_volo: int
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""
                WITH flight_data AS (
                    SELECT  
                        MARCHE AS marche, 
                        data_ora_decollo AS start_datetime,  
                        data_ora_atterraggio AS end_datetime 
                    FROM 
                        ETL.VOLI 
                    WHERE 
                        ID_VOLO = {id_volo}
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.MARCHE AS marche
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN flight_data fd
                        ON msg.MARCHE = fd.marche
                        AND msg.datetime_message BETWEEN fd.start_datetime  AND fd.end_datetime 
                    WHERE TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                    AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    AND msg.mqtt_channel = 'N'
                    AND msg.flag_gps = '1'
                        ),
                grouped_7 AS (
                        SELECT
                            MAX(marche) AS marche,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.vcc,
                            g7.icc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                    ),
                    final0 AS (
                        SELECT 
                            (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                            (f.altitude - f.elevation) AS height,
                            f.*
                        FROM final1 f
                        )
                        SELECT 
                            f.*,
                            (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                            (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                            (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                            (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                            (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                            (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                            (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                            (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                        AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                        (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                        OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                            
                            (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                                    AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                                    THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                                    
                            (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                    AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                    AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                        AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                            AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                    THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                        FROM
                            final0 f
                        JOIN 
                            base.box_alarm b
                            ON f.marche = b.marche     
            """
        return self.__manager.get_query_result(query)
    
    
    def get_telemetry_by_marca_datetime_interval(
        self, marca: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
                WITH base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE
                        msg.marche = ?
                        AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2')
                    ),
                grouped_7 AS (
                        SELECT
                            MAX(marche) AS marche,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                    ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )
                    SELECT 
                        f.*,
                        (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                        (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                        (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                        (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                        (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                        (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                        (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                    AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                    (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                    OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                        
                       (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                                
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                    FROM
                        final0 f
                    INNER JOIN base.box_alarm b ON f.marche = b.marche
                """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])
    

    def get_alarm_by_marca(self, marca: str):
        """
        Retrieves telemetry data for a specific airplane.

        The data is grouped by seconds, and for each second, the following are available: GPS data, AHRS, VCC, ICC, TEMPERATURE_BOX, and MAGNETIC_HEADING, along with a elevationfield that represents the terrain elevation measured by the barometric sensor.

        If there is no data for a certain second, the gps_payloadfield will be None.

        :param brand: Airplane code
        :return: A generator of tuples containing the requested information
        """
    
        query = f"""
                WITH base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE msg.marche = ?
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V')
                ),
                grouped_7 AS (
                        SELECT
                            MAX(marche) AS marche,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message 
                    ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                    ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )      
                SELECT 
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
            """
        return self.__manager.get_query_result(query, [marca])
    
    def get_alarms_by_marca(self, marca: str):
        """
        Retrieves telemetry data for a specific airplane.

        The data is grouped by seconds, and for each second, the following are available: GPS data, AHRS, VCC, ICC, TEMPERATURE_BOX, and MAGNETIC_HEADING, along with a elevationfield that represents the terrain elevation measured by the barometric sensor.

        If there is no data for a certain second, the gps_payloadfield will be None.

        :param brand: Airplane code
        :return: A generator of tuples containing the requested information
        """
    
        query = f"""
                WITH base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE msg.marche = ?
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V')
                ),
                grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data  
                    GROUP BY datetime_message 
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                )      
                SELECT 
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
            """
        return self.__manager.get_query_result(query, [marca])

    def get_telemetry_by_marca(self, marca: str):
        """
        Retrieves telemetry data for a specific airplane.

        The data is grouped by seconds, and for each second, the following are available: GPS data, AHRS, VCC, ICC, TEMPERATURE_BOX, and MAGNETIC_HEADING, along with a elevationfield that represents the terrain elevation measured by the barometric sensor.

        If there is no data for a certain second, the gps_payloadfield will be None.

        :param brand: Airplane code
        :return: A generator of tuples containing the requested information
        """
    
        query = f"""
               WITH base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE
                        msg.marche = ?
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                ),  
            grouped_7 AS (
                SELECT
                    MAX(marche) AS marche,
                    datetime_message AS date_time,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                FROM
                    base_data   
                GROUP BY datetime_message
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.vcc,
                        g7.icc,
                        g7.ahrs_payload, 
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )
                    SELECT 
                        f.*,
                        (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                        (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                        (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                        (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                        (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                        (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                        (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                    AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                    (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                    OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                        
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                                
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                    FROM
                        final0 f   
                    JOIN
                        base.box_alarm b ON f.marche = b.marche
            """
        return self.__manager.get_query_result(query, params=(marca,))

    def get_alarms_by_mutiple_marcas_datetime_interval(
        self, marcas: tuple, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        marcas = list(marcas)
        placeholders = ", ".join("?" for _ in marcas)
        query = f""" 
        
            WITH base_data AS (
                SELECT
                    msg.MARCHE,  -- Include the MARCHE column here for filtering
                    msg.datetime_message,
                    msg.mqtt_channel,
                    msg.mqtt_subtopic,
                    msg.payload_alfa
                FROM
                    etl.etl_mqtt_message msg
                JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                WHERE
                    msg.MARCHE IN ({placeholders})
                    AND msg.flag_gps = '1' 
                    AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                    AND msg.mqtt_subtopic IN ('5', '6', '7', 'V') 
                    AND msg.mqtt_channel = 'N'
                    AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                    ),
                grouped_7 AS (
                    SELECT
                        marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data  
                    GROUP BY marche, datetime_message 
                ), 
                final1 AS (
                SELECT
                    g7.marche,
                    g7.date_time,
                    g7.gps_payload,
                    g7.ahrs_payload, 
                    REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                    REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                    SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                    SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                    SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                    SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                    SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                    SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                    g7.vertical_speed,
                    g7.magnetic_heading,
                    e.payload_alfa AS elevation
                FROM grouped_7 g7
                    LEFT JOIN LATERAL (
                        SELECT e1.payload_alfa
                        FROM etl.etl_mqtt_message e1
                        WHERE e1.marche = g7.marche
                            AND e1.mqtt_channel = 'E'
                            AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                            AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                        ORDER BY e1.datetime_message DESC
                        FETCH FIRST 1 ROW ONLY
                    ) AS e ON 1=1
            ),
            final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )    
                SELECT 
                    f.marche as registration,
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                            AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                            AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b ON f.marche = b.marche
                GROUP BY f.marche
        """       
        return self.__manager.get_query_result(query, list(marcas) + [start_datetime, end_datetime])

    def get_telemetry_alarms_by_mutiple_marcas_datetime_interval(
        self, marcas: tuple, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        marcas = list(marcas)
        placeholders = ", ".join("?" for _ in marcas)
        query = f""" 
                WITH base_data AS (
                    SELECT
                        msg.MARCHE,  -- Include the MARCHE column here for filtering
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE
                        msg.MARCHE IN ({placeholders})
                        AND msg.flag_gps = '1' 
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                        AND msg.mqtt_channel = 'N'
                        AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        ),
                    grouped_7 AS (
                        SELECT
                            marche,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data 
                        GROUP BY marche, datetime_message   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.icc,
                        g7.vcc,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )   
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f 
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche  
        """        
        return self.__manager.get_query_result(query, list(marcas) + [start_datetime, end_datetime])
    
    
    def get_telemetry_alarms_datetime_interval(
        self, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f""" 
        
                WITH base_data AS (
                    SELECT
                        msg.MARCHE,  -- Include the MARCHE column here for filtering
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE
                        1=1 
                        AND msg.flag_gps = '1' 
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                        AND msg.mqtt_channel = 'N'
                        AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        ),
                    grouped_7 AS (
                        SELECT
                            marche,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data 
                        GROUP BY marche, datetime_message   
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                    ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )   
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f 
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche  
        """        
        return self.__manager.get_query_result(query, [start_datetime, end_datetime])
    
    def get_telemetry_alarms_by_flight(
        self, id_volo: int
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        proc_name = 'BASE.TELEMETRYALARMSBYFLIGHTID'
        params = id_volo
        pquery = f"CALL {proc_name}({params})"
        
        query = f""" 
                  WITH flight_data AS (
                    SELECT  
                        MARCHE AS marche, 
                        data_ora_decollo AS start_datetime,  
                        data_ora_atterraggio AS end_datetime 
                    FROM 
                        ETL.VOLI 
                    WHERE 
                        ID_VOLO = {id_volo}
                ),
                base_data AS (
                    SELECT
                        datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.MARCHE AS marche
                    FROM
                        etl.etl_mqtt_message msg
                    INNER JOIN flight_data fd
                        ON msg.MARCHE = fd.marche
                        AND msg.datetime_message BETWEEN fd.start_datetime  AND fd.end_datetime 
                    WHERE TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                    AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    AND msg.mqtt_channel = 'N'
                    AND msg.flag_gps = '1'
                ),
                grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data 
                    GROUP BY datetime_message   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.icc,
                        g7.vcc,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                    ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
        """
        return self.__manager.get_query_result(query)
    
    
    
    def get_alarms_by_flight(
        self, id_volo: int
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f""" 
                WITH flight_data AS (
                    SELECT  
                        MARCHE AS marche, 
                        data_ora_decollo AS start_datetime,  
                        data_ora_atterraggio AS end_datetime 
                    FROM 
                        ETL.VOLI 
                    WHERE 
                        ID_VOLO = {id_volo}
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.MARCHE AS marche
                    FROM
                        etl.etl_mqtt_message msg
                    INNER JOIN flight_data fd
                        ON msg.MARCHE = fd.marche
                        AND msg.datetime_message BETWEEN fd.start_datetime AND fd.end_datetime 
                    WHERE TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                    AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    AND msg.mqtt_channel = 'N'
                    AND msg.flag_gps = '1'
                ),
                grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data 
                    GROUP BY datetime_message   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                )
                SELECT 
                    MAX(f.marche) as registration,
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                ON f.marche = b.marche
        """
        return self.__manager.get_query_result(query)

    def get_flightswithalarms_by_marca_datetime_interval(
        self, marca: str, start_datetime: str, end_datetime: str 
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
            WITH base_data AS (
                SELECT
                    voli.ID_VOLO AS id_volo,
                    msg.datetime_message,
                    msg.mqtt_channel,
                    msg.mqtt_subtopic,
                    msg.payload_alfa,
                    msg.marche
                FROM
                    etl.etl_mqtt_message msg 
                JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                WHERE
                    msg.marche = ?
                    AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                    AND msg.FLAG_GPS = '1'
                    AND TRANSLATE(msg.PAYLOAD_ALFA, '', '0123456789,.-+') = ''
                    AND msg.MQTT_SUBTOPIC IN ('5', '6', '7', 'V')
                    AND msg.MQTT_CHANNEL = 'N'
            ),
            grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        id_volo,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data 
                    GROUP BY datetime_message, id_volo  
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.id_volo,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
            ),
            final0 AS (
                    SELECT 
                        (SQRT(POWER(acc_x, 2) + POWER(acc_y, 2) + POWER(acc_z, 2))) AS g_tot,
                        (altitude - elevation) AS height,
                        f.*
                    FROM final1 f
                    ),                
            telemtery_data AS (
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max})) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
            FROM
                final0 f    
            JOIN 
                base.box_alarm b
                ON f.marche = b.marche
            )              
            SELECT  
                COUNT(DISTINCT id_volo) as numberoflights 
            FROM
                telemtery_data
            WHERE alarm_g_tot > 0 OR alarm_ground_speed > 0 OR alarm_vertical_speed > 0 OR alarm_pitch > 0 OR alarm_roll > 0 OR alarm_altitude > 0 OR alarm_hard_landing > 0 OR alarm_high_roll_at_low_height > 0 OR alarm_high_pitch_at_low_height_with_low_acceleration > 0 OR alarm_low_ground_speed_at_low_height_with_low_acceleration > 0 
        """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])
    

    def get_top_flightswithalarms_by_marca_datetime_interval(
        self, top:str, marca: str, start_datetime: str, end_datetime: str 
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
            WITH base_data AS (
                SELECT
                    voli.ID_VOLO AS id_volo,
                    msg.datetime_message,
                    msg.mqtt_channel,
                    msg.mqtt_subtopic,
                    msg.payload_alfa,
                    msg.marche
                FROM
                    etl.etl_mqtt_message msg 
                JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                WHERE
                    msg.marche = ?
                    AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                    AND msg.FLAG_GPS = '1'
                    AND TRANSLATE(msg.PAYLOAD_ALFA, '', '0123456789,.-+') = ''
                    AND msg.MQTT_SUBTOPIC IN ('5', '6', '7', 'V')
                    AND msg.MQTT_CHANNEL = 'N'
            ),
            grouped_7 AS (
                SELECT
                    MAX(marche) AS marche,
                    datetime_message AS date_time,
                    id_volo,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                    MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                FROM
                    base_data 
                GROUP BY datetime_message, id_volo   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.id_volo,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
            final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    ),               
            telemetery_data AS (
                SELECT 
                    f.marche, 
                    f.id_volo,
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b ON f.marche = b.marche
                GROUP BY f.marche, f.id_volo
            ) 
            SELECT
                marche, 
                id_volo,
                g_tot,
                ground_speed,
                vertical_speed,
                pitch,
                roll,
                altitude,
                hard_landing,
                high_roll_at_low_height,
                low_ground_speed_at_low_height_with_low_acceleration,
                high_pitch_at_low_height_with_low_acceleration,
                (g_tot + ground_speed + vertical_speed + pitch + roll + altitude + hard_landing +
                high_roll_at_low_height + low_ground_speed_at_low_height_with_low_acceleration + high_pitch_at_low_height_with_low_acceleration) AS total_alarms
            FROM telemetery_data
            ORDER BY total_alarms DESC
            LIMIT {int(top)}
        """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])
        
    def get_alarms_by_marca_datetime_interval(
        self, marca: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        proc_name = 'BASE.TEST'
        params = (marca,start_datetime,end_datetime)
        pp_query = f"CALL {proc_name}{params}"
        
        query = f"""
            WITH base_data AS (
            SELECT
                msg.MARCHE,  -- Include the MARCHE column here for filtering
                datetime_message,
                msg.mqtt_channel,
                msg.mqtt_subtopic,
                msg.payload_alfa
            FROM
                etl.etl_mqtt_message msg
            JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
            WHERE
                msg.marche = ?
                AND msg.flag_gps = '1' 
                AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                AND msg.mqtt_subtopic IN ('5', '6', '7', 'V') 
                AND msg.mqtt_channel = 'N'
                AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                ),
                grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data 
                    GROUP BY datetime_message   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
            final0 AS (
            SELECT 
                (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                (f.altitude - f.elevation) AS height,
                f.*
            FROM final1 f
            )
            SELECT 
                    MAX(f.marche) as registration,
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                            AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche 
        """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])

    def get_telemetry_alarms_by_marca_datetime_interval(
        self, marca: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
                WITH base_data AS (
                    SELECT
                        msg.MARCHE,  -- Include the MARCHE column here for filtering
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE
                        msg.marche = ?
                        AND msg.flag_gps = '1' 
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                        AND msg.mqtt_channel = 'N'
                        AND msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        ),
                grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data 
                    GROUP BY datetime_message   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.icc,
                        g7.vcc,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche  
                """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])

    def get_telemetry_alarms_by_marca(self, marca: str):
        """
        Retrieves the telemetry of a given marca, including the alarms raised during the flight and the labels assigned to the telemetry points.

        Args:
            marca (str): The marca to filter by.

        Returns:
            generator: A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f""" 
                WITH base_data AS (
                    SELECT
                        msg.MARCHE,  -- Include the MARCHE column here for filtering
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN etl.voli voli ON msg.MARCHE = voli.MARCHE AND (msg.datetime_message BETWEEN voli.data_ora_decollo AND voli.data_ora_atterraggio)
                    WHERE
                        msg.marche = ?
                        AND msg.flag_gps = '1' 
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                        AND msg.mqtt_channel = 'N'
                        ),
                grouped_7 AS (
                    SELECT
                        MAX(marche) AS marche,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data 
                    GROUP BY datetime_message   
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.icc,
                        g7.vcc,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max})) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM 
                    final0 f
                JOIN
                    base.box_alarm b ON f.marche = b.marche  
        """
        return self.__manager.get_query_result(query, [marca])



class PilotTelemetryMQTTDatabaseAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        """
        Constructor for TelemetryMQTTDatabaseAccess.

        :param manager: A DatabaseManager object, used to query the database.
        :type manager: DatabaseManager
        :return: No return value
        :rtype: None
        """
        self.__manager = manager
        self.flight_envelope = FlightEnvelope()

    def get_telemetry_by_datetime_interval_unformatted(
        self, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given datetime interval.

        The data is not formatted in any way, and is returned as is from the database.

        Parameters
        ----------
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = """SELECT * FROM ETL.ETL_MQTT_MESSAGE
                    WHERE DATETIME_MESSAGE >= ? AND DATETIME_MESSAGE <= ?
                    AND MQTT_CHANNEL IN ('N', 'E') AND MQTT_SUBTOPIC IN ('0', '1', '2','5', '6','7','9', 'V', '-')
                """
        return self.__manager.get_query_result(query, [start_datetime, end_datetime])

    def get_telemetry_by_pilot_datetime_interval_unformatted(
        self, pilot: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is not formatted in any way, and is returned as is from the database.

        Parameters
        ----------
        pilot : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""SELECT msg.* FROM ETL.ETL_MQTT_MESSAGE msg
                    JOIN 
                        (SELECT 
                            CV.CODCF_PAGANTE AS pilot,
                            CV.MARCHE AS MARCHE,
                            TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                            TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                            TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                            TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                        FROM 
                            CLUB.CVOLATO CV
                        ) voli ON msg.MARCHE = voli.MARCHE 
                    WHERE voli.pilot = ?
                        AND msg.DATETIME_MESSAGE >= ? AND msg.DATETIME_MESSAGE <= ?
                        AND msg.MQTT_CHANNEL IN ('N', 'E') AND msg.MQTT_SUBTOPIC IN ('0', '1', '2','5', '6','7','9', 'V', '-')
                """
        return self.__manager.get_query_result(query, [pilot, start_datetime, end_datetime])

    def get_telemetry_by_pilot_unformatted(self, pilot: str):
        """
        Retrieves all telemetry data from the database for the given marca.

        The data is not formatted in any way, and is returned as is from the database.

        Parameters
        ----------
        pilot : str
            The marca to filter by.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""SELECT msg.* FROM ETL.ETL_MQTT_MESSAGE msg
                    JOIN 
                        (SELECT 
                            CV.CODCF_PAGANTE AS pilot,
                            CV.MARCHE AS MARCHE,
                            TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                            TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                            TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                            TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                        FROM 
                            CLUB.CVOLATO CV
                        ) voli ON msg.MARCHE = voli.MARCHE 
                    WHERE voli.pilot = ?
                        AND msg.MQTT_CHANNEL IN ('N', 'E') AND MQTT_SUBTOPIC IN ('0', '1', '2','5', '6','7','9', 'V', '-')
                """
        return self.__manager.get_query_result(query, [pilot])
    
    def get_telemetry_by_pilots_datetime_interval(
        self, pilots: list, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        pilots : list[str]
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        pilots = list(pilots)
        placeholders = ", ".join("?" for _ in pilots)
        query = f"""
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE IN ({placeholders})
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                    ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )
                    SELECT 
                        f.*,
                        (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                        (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                        (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                        (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                        (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                        (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                        (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                    AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                    (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                    OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                        
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                                AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                                THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                                
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                    FROM
                        final0 f
                    INNER JOIN base.box_alarm b ON f.marche = b.marche
                """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])

    def get_telemetry_by_flight(
        self, id_volo: int
    ):
        """
        Retrieves all telemetry data from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""
            WITH pilot_flights AS (
                SELECT 
                    CV.CODCF_PAGANTE AS pilot,
                    CV.MARCHE AS marche,
                    TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                    TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                    TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                    TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                FROM 
                    CLUB.CVOLATO CV
                WHERE 
                    CV.ID = {id_volo}
            ),
            base_data AS (
                SELECT
                    msg.datetime_message,
                    msg.mqtt_channel,
                    msg.mqtt_subtopic,
                    msg.payload_alfa,
                    msg.marche,
                    pf.pilot
                FROM
                    etl.etl_mqtt_message msg
                JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                    AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                WHERE msg.flag_gps = '1'
                    AND msg.mqtt_channel = 'N'
                    AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                    AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                ),  
            grouped_7 AS (
                    SELECT
                        marche,
                        MAX(pilot) AS pilot,
                        datetime_message AS date_time,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                        MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                    FROM
                        base_data  
                    GROUP BY datetime_message, marche 
                ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.pilot,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.icc,
                        g7.vcc,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
            ),
            final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                      
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche     
            """
        return self.__manager.get_query_result(query)
    
    
    def get_telemetry_by_pilot_datetime_interval(
            self, pilot: str, start_datetime: str, end_datetime: str
        ):
        """
        Retrieves all telemetry data from the database for the given pilot and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        pilot_code : str
            The pilot code (CODCF_PAGANTE) to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
    
        query = f"""
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                    ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )
                    SELECT 
                        f.*,
                        (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                        (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                        (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                        (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                        (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                        (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                        (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                    AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                    (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                    OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                        
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                                
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                    FROM
                        final0 f
                    INNER JOIN base.box_alarm b ON f.marche = b.marche
                """
        return self.__manager.get_query_result(query, [marca, start_datetime, end_datetime])
    

    def get_alarm_by_pilot(self, pilot: str):
        """
        Retrieves telemetry data for a specific airplane.

        The data is grouped by seconds, and for each second, the following are available: GPS data, AHRS, VCC, ICC, TEMPERATURE_BOX, and MAGNETIC_HEADING, along with a elevationfield that represents the terrain elevation measured by the barometric sensor.

        If there is no data for a certain second, the gps_payloadfield will be None.

        :param brand: Airplane code
        :return: A generator of tuples containing the requested information
        """
    
        query = f"""
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )      
                SELECT 
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
            """
        return self.__manager.get_query_result(query, [pilot])
    
    def get_alarms_by_pilot(self, pilot: str):
        """
        Retrieves telemetry data for a specific airplane.

        The data is grouped by seconds, and for each second, the following are available: GPS data, AHRS, VCC, ICC, TEMPERATURE_BOX, and MAGNETIC_HEADING, along with a elevationfield that represents the terrain elevation measured by the barometric sensor.

        If there is no data for a certain second, the gps_payloadfield will be None.

        :param brand: Airplane code
        :return: A generator of tuples containing the requested information
        """
    
        query = f"""
                  WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )      
                SELECT 
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
            """
        return self.__manager.get_query_result(query, [pilot])

    def get_telemetry_by_pilot(self, pilot: str):
        """
        Retrieves telemetry data for a specific airplane.

        The data is grouped by seconds, and for each second, the following are available: GPS data, AHRS, VCC, ICC, TEMPERATURE_BOX, and MAGNETIC_HEADING, along with a elevationfield that represents the terrain elevation measured by the barometric sensor.

        If there is no data for a certain second, the gps_payloadfield will be None.

        :param brand: Airplane code
        :return: A generator of tuples containing the requested information
        """
    
        query = f"""
                  WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = {pilot}
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                final1 AS (
                    SELECT
                        g7.marche,
                        g7.pilot,
                        g7.date_time,
                        g7.gps_payload,
                        g7.ahrs_payload, 
                        g7.icc,
                        g7.vcc,
                        REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                        REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                        SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                        SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                        SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                        SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                        SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                        SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                        g7.vertical_speed,
                        g7.magnetic_heading,
                        e.payload_alfa AS elevation
                    FROM grouped_7 g7
                        LEFT JOIN LATERAL (
                            SELECT e1.payload_alfa
                            FROM etl.etl_mqtt_message e1
                            WHERE e1.marche = g7.marche
                                AND e1.mqtt_channel = 'E'
                                AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                            ORDER BY e1.datetime_message DESC
                            FETCH FIRST 1 ROW ONLY
                        ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                    )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                        AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                        AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                            AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                        THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f   
                JOIN 
                    base.box_alarm b ON f.marche = b.marche  
            """
        return self.__manager.get_query_result_generator(query)
    
    def get_alarms_by_mutiple_pilots_datetime_interval(
        self, pilots: list, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        pilots = list(pilots)
        placeholders = ", ".join("?" for _ in pilots)
        query = f""" 
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE IN ({placeholders})
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                    ),
                    final0 AS (
                        SELECT 
                            (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                            (f.altitude - f.elevation) AS height,
                            f.*
                        FROM final1 f
                        )    
                        SELECT 
                            f.marche as registration,
                            SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                            SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                            SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                            SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                            SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                            SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                            SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                            SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                        AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                        (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                        OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                        
                            SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                                    AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                                    THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                                    
                            SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                    AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                    AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                        AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                            AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                    THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                        FROM
                            final0 f    
                        JOIN 
                            base.box_alarm b ON f.marche = b.marche
                        GROUP BY f.marche
                """       
        return self.__manager.get_query_result(query, list(pilots) + [start_datetime, end_datetime])

    def get_telemetry_alarms_by_mutiple_pilots_datetime_interval(
        self, pilots: tuple, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        pilot : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        pilots = list(pilots)
        placeholders = ", ".join("?" for _ in pilots)
        query = f""" 
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE IN ({placeholders})
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )   
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f 
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche  
        """        
        return self.__manager.get_query_result(query, list(pilots) + [start_datetime, end_datetime])
    
    
    def get_telemetry_alarms_datetime_interval(
        self, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f""" 
        
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )   
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f 
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche  
        """        
        return self.__manager.get_query_result(query, [start_datetime, end_datetime])
    
    def get_telemetry_alarms_by_flight(
        self, id_volo: int
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f""" 
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE CV.ID = {id_volo}
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
        """
        return self.__manager.get_query_result(query)
    
    
    
    def get_alarms_by_flight(
        self, id_volo: int
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f""" 
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE CV.ID = {id_volo}
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                    SELECT 
                        (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                        (f.altitude - f.elevation) AS height,
                        f.*
                    FROM final1 f
                )
                SELECT 
                    f.marche AS registration,
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                    			(f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                    		AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                    		AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                ON f.marche = b.marche
                GROUP BY f.marche
        """
        return self.__manager.get_query_result(query)

    def get_flightswithalarms_by_pilot_datetime_interval(
        self, pilot: str, start_datetime: str, end_datetime: str 
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        pilot : str
            The pilot to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
                WITH pilot_flights AS (
                    SELECT 
                        CV.ID AS id_volo, 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot, 
                        pf.id_volo
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            id_volo, 
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche, id_volo
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.id_volo,
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                        SELECT 
                            (SQRT(POWER(acc_x, 2) + POWER(acc_y, 2) + POWER(acc_z, 2))) AS g_tot,
                            (altitude - elevation) AS height,
                            f.*
                        FROM final1 f
                        ),                
                telemtery_data AS (
                    SELECT 
                        f.*,
                        (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                        (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                        (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                        (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                        (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                        (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                        (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                    AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                    (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                    OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max})) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                        
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                                AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                                THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                                
                        (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                                AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                                AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                    AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                        AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                                THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche
                )              
                SELECT  
                    COUNT(DISTINCT id_volo) AS numberoflights 
                FROM
                    telemtery_data
                WHERE alarm_g_tot > 0 OR alarm_ground_speed > 0 OR alarm_vertical_speed > 0 OR alarm_pitch > 0 OR alarm_roll > 0 OR alarm_altitude > 0 OR alarm_hard_landing > 0 OR alarm_high_roll_at_low_height > 0 OR alarm_high_pitch_at_low_height_with_low_acceleration > 0 OR alarm_low_ground_speed_at_low_height_with_low_acceleration > 0 
            """
        return self.__manager.get_query_result(query, [pilot, start_datetime, end_datetime])
    

    def get_top_flightswithalarms_by_pilot_datetime_interval(
        self, top:str, pilot: str, start_datetime: str, end_datetime: str 
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        pilot : str
            The pilot to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
                WITH pilot_flights AS (
                    SELECT 
                        CV.ID AS id_volo, 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE CV.CODCF_PAGANTE = ?
                ), 
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot, 
                        pf.id_volo
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            id_volo, 
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche, id_volo
                    ), 
                    final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.id_volo,
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                        ),
                    final0 AS (
                            SELECT 
                                (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                                (f.altitude - f.elevation) AS height,
                                f.*
                            FROM final1 f
                            ),               
                    telemetery_data AS (
                        SELECT 
                            f.marche, 
                            f.id_volo,
                            SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                            SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                            SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                            SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                            SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                            SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                            SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                            SUM(CASE WHEN ((f.height > 30 
                                        AND f.height < 100) AND
                                        (f.roll < -40 
                                        OR f.roll > 40) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                        
                            SUM(CASE WHEN ((f.height > 30 AND f.height < 100) 
                                    AND (f.ground_speed < 50) 
                                    AND (-0.001 > f.acc_x 
                                        AND f.acc_x < 0.001))
                                    THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                                    
                            SUM(CASE WHEN ((f.height > 30 AND f.height < 100)
                                    AND (f.pitch < -10) 
                                    AND (f.pitch > 10) 
                                        AND (-0.001 > f.acc_x 
                                            AND f.acc_x < 0.001)) 
                                    THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                        FROM
                            final0 f    
                        JOIN 
                            base.box_alarm b ON f.marche = b.marche
                        GROUP BY f.marche, f.id_volo
                    ) 
                    SELECT
                        marche, 
                        id_volo,
                        g_tot,
                        ground_speed,
                        vertical_speed,
                        pitch,
                        roll,
                        altitude,
                        hard_landing,
                        high_roll_at_low_height,
                        low_ground_speed_at_low_height_with_low_acceleration,
                        high_pitch_at_low_height_with_low_acceleration,
                        (g_tot + ground_speed + vertical_speed + pitch + roll + altitude + hard_landing +
                        high_roll_at_low_height + low_ground_speed_at_low_height_with_low_acceleration + high_pitch_at_low_height_with_low_acceleration) AS total_alarms
                    FROM telemetery_data
                    ORDER BY total_alarms DESC
                    LIMIT {int(top)}
            """
        return self.__manager.get_query_result(query, [pilot, start_datetime, end_datetime])
        
    def get_alarms_by_pilot_datetime_interval(
        self, pilot: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        marca : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """

        
        query = f"""
                 WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )
                SELECT 
                    f.marche AS registration,
                    SUM(CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS g_tot,
                    SUM(CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS ground_speed,
                    SUM(CASE WHEN ABS(f.vertical_speed) > b.vsi_max  THEN 1 ELSE 0 END) AS vertical_speed,
                    SUM(CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS pitch,
                    SUM(CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS roll,
                    SUM(CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS altitude,
                    SUM(CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS hard_landing,                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS high_roll_at_low_height,
                                
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                            AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS low_ground_speed_at_low_height_with_low_acceleration,
                            
                    SUM(CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                    ON f.marche = b.marche 
                GROUP BY f.marche
        """
        return self.__manager.get_query_result(query, [pilot, start_datetime, end_datetime])

    def get_telemetry_alarms_by_pilot_datetime_interval(
        self, pilot: str, start_datetime: str, end_datetime: str
    ):
        """
        Retrieves all telemetry alarms from the database for the given marca and datetime interval.

        The data is returned as a formatted pandas DataFrame, with columns for each of the telemetry fields.

        Parameters
        ----------
        pilot : str
            The marca to filter by.
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        
        query = f"""
                 WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE
                        msg.datetime_message BETWEEN (TIMESTAMP(CAST(? AS VARCHAR(26))) - 5 MINUTES) AND (TIMESTAMP(CAST(? AS VARCHAR(26))) + 5 MINUTES)
                        AND msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max}) ) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM
                    final0 f    
                JOIN 
                    base.box_alarm b
                ON f.marche = b.marche  
            """
        return self.__manager.get_query_result(query, [pilot, start_datetime, end_datetime])

    def get_telemetry_alarms_by_pilot(self, pilot: str):
        """
        Retrieves the telemetry of a given pilot, including the alarms raised during the flight and the labels assigned to the telemetry points.

        Args:
            pilot (str): The pilot to filter by.

        Returns:
            generator: A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f""" 
                WITH pilot_flights AS (
                    SELECT 
                        CV.CODCF_PAGANTE AS pilot,
                        CV.MARCHE AS marche,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_TAKEOFF) AS block_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.BLOCK_LANDING) AS block_landing,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_TAKEOFF) AS stick_takeoff,
                        TIMESTAMP(CV.DATA_VOLO, CV.STICK_LANDING) AS stick_landing
                    FROM 
                        CLUB.CVOLATO CV
                    WHERE 
                        CV.CODCF_PAGANTE = ?
                ),
                base_data AS (
                    SELECT
                        msg.datetime_message,
                        msg.mqtt_channel,
                        msg.mqtt_subtopic,
                        msg.payload_alfa,
                        msg.marche,
                        pf.pilot
                    FROM
                        etl.etl_mqtt_message msg
                    JOIN pilot_flights pf ON msg.MARCHE = pf.marche 
                        AND (msg.datetime_message BETWEEN pf.block_takeoff AND pf.block_landing)
                    WHERE msg.flag_gps = '1'
                        AND msg.mqtt_channel = 'N'
                        AND TRANSLATE(msg.payload_alfa, '', '0123456789,.-+') = ''
                        AND msg.mqtt_subtopic IN ('5', '6', '7', 'V', '0', '1', '2') 
                    ),  
                grouped_7 AS (
                        SELECT
                            marche,
                            MAX(pilot) AS pilot,
                            datetime_message AS date_time,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '7' THEN payload_alfa END) AS gps_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '6' THEN payload_alfa END) AS ahrs_payload,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '0' THEN payload_alfa END) AS vcc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '1' THEN payload_alfa END) AS icc,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = '5' THEN payload_alfa END) AS magnetic_heading,
                            MAX(CASE WHEN mqtt_channel = 'N' AND mqtt_subtopic = 'V' THEN payload_alfa END) AS vertical_speed
                        FROM
                            base_data  
                        GROUP BY datetime_message, marche 
                    ), 
                final1 AS (
                        SELECT
                            g7.marche,
                            g7.pilot,
                            g7.date_time,
                            g7.gps_payload,
                            g7.ahrs_payload, 
                            g7.icc,
                            g7.vcc,
                            REGEXP_SUBSTR(g7.gps_payload, '^[^,]+') AS latitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 2) AS longitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 3) AS altitude,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 4) AS ground_speed,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+', 1, 5) AS heading,
                            REGEXP_SUBSTR(g7.gps_payload, '[^,]+$', 1, 1) AS data_valid,
                            SUBSTRING(g7.ahrs_payload, 1, 4) AS pitch,
                            SUBSTRING(g7.ahrs_payload, 5, 4) AS roll,
                            SUBSTRING(g7.ahrs_payload, 9, 5) AS acc_y,
                            SUBSTRING(g7.ahrs_payload, 14, 5) AS acc_x,
                            SUBSTRING(g7.ahrs_payload, 19, 5) AS acc_z,
                            SUBSTRING(g7.ahrs_payload, 24, 4) AS turn_rate,
                            g7.vertical_speed,
                            g7.magnetic_heading,
                            e.payload_alfa AS elevation
                        FROM grouped_7 g7
                            LEFT JOIN LATERAL (
                                SELECT e1.payload_alfa
                                FROM etl.etl_mqtt_message e1
                                WHERE e1.marche = g7.marche
                                    AND e1.mqtt_channel = 'E'
                                    AND e1.datetime_message BETWEEN g7.date_time AND ADD_SECONDS(g7.date_time, 300)
                                    AND TRANSLATE(e1.payload_alfa, '', '0123456789,.-+') = ''
                                ORDER BY e1.datetime_message DESC
                                FETCH FIRST 1 ROW ONLY
                            ) AS e ON 1=1
                ),
                final0 AS (
                SELECT 
                    (SQRT(POWER(f.acc_x, 2) + POWER(f.acc_y, 2) + POWER(f.acc_z, 2))) AS g_tot,
                    (f.altitude - f.elevation) AS height,
                    f.*
                FROM final1 f
                )
                SELECT 
                    f.*,
                    (CASE WHEN (f.g_tot > b.gtot_max) THEN 1 ELSE 0 END) AS alarm_g_tot,
                    (CASE WHEN ABS(f.ground_speed) > b.ias_max THEN 1 ELSE 0 END) AS alarm_ground_speed,
                    (CASE WHEN ABS(f.vertical_speed) > b.vsi_max THEN 1 ELSE 0 END) AS alarm_vertical_speed,
                    (CASE WHEN ABS(f.pitch) > b.pitch_max THEN 1 ELSE 0 END) AS alarm_pitch,
                    (CASE WHEN ABS(f.roll) > b.roll_max THEN 1 ELSE 0 END) AS alarm_roll,
                    (CASE WHEN f.altitude > b.altitude_max THEN 1 ELSE 0 END) AS alarm_altitude,
                    (CASE WHEN (f.height < 15 AND f.acc_y > 1.6) THEN 1 ELSE 0 END) AS alarm_hard_landing,
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} 
                                AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) AND
                                (f.roll < {self.flight_envelope.get_low_height_limits().roll_min} 
                                OR f.roll > {self.flight_envelope.get_low_height_limits().roll_max})) THEN 1 ELSE 0 END) AS alarm_high_roll_at_low_height,
                                    
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()}) 
                            AND (f.ground_speed < {self.flight_envelope.get_low_height_limits().ground_speed_min}) 
                            AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]}))
                            THEN 1 ELSE 0 END) AS alarm_low_ground_speed_at_low_height_with_low_acceleration,
                            
                    (CASE WHEN ((f.height > {self.flight_envelope.get_low_height_lower_limit()} AND f.height < {self.flight_envelope.get_low_height_upper_limit()})
                            AND (f.pitch < {self.flight_envelope.get_low_height_limits().pitch_min}) 
                            AND (f.pitch > {self.flight_envelope.get_low_height_limits().pitch_max}) 
                                AND ({self.flight_envelope.get_low_height_limits().acc_x_danger_range[0]} > f.acc_x 
                                    AND f.acc_x < {self.flight_envelope.get_low_height_limits().acc_x_danger_range[1]})) 
                            THEN 1 ELSE 0 END) AS alarm_high_pitch_at_low_height_with_low_acceleration
                FROM 
                    final0 f
                JOIN
                    base.box_alarm b ON f.marche = b.marche  
        """
        return self.__manager.get_query_result(query, [pilot])

