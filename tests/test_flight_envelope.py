from datamodels import TelemetrySample
from logic.flight_envelope import FlightEnvelopeChecker

# Limits pulled from flight_envelope_limits.yaml (low_height_envelope_limits):
#   pitch_min: -10, pitch_max: 10
#   acc_x_danger_range: [-0.001, 0.001]
#   roll_min: -40, roll_max: 40
#   ground_speed_min: 50
#   low_height_upper_limit: 100
#
# Note: TelemetrySample.pitch negates whatever is assigned via the setter, so a
# telemetry pitch reading of `target` is produced by setting `.pitch = -target`.

ALARM = "high_pitch_at_low_height_with_low_acceleration"

ACC_X_IN_DANGER_RANGE = 0.0005  # inside [-0.001, 0.001]
ACC_X_SAFE = 5.0  # outside [-0.001, 0.001]


def make_sample(*, pitch_reading: float, acc_x: float) -> TelemetrySample:
    """Build a telemetry sample that is inside the low-height envelope and safe
    on every axis except pitch, so only the pitch-exceedance branch is exercised."""
    sample = TelemetrySample()
    sample.height = 50  # below low_height_upper_limit (100) -> low-height checks apply
    sample.roll = 0  # within [-40, 40] -> no roll alarm
    sample.ground_speed = 100  # above ground_speed_min (50) -> no ground-speed alarm
    sample.acc_x = acc_x
    sample.pitch = -pitch_reading  # counteract the getter's negation
    return sample


def test_high_pitch_alarms_when_acc_x_in_danger_range():
    """Positive mirror: pitch above max + acc_x in danger range -> alarm."""
    sample = make_sample(pitch_reading=15, acc_x=ACC_X_IN_DANGER_RANGE)

    result = FlightEnvelopeChecker().check(sample)

    assert result.alarms is not None
    assert ALARM in result.alarms


def test_high_pitch_does_not_alarm_when_acc_x_safe():
    """Positive mirror: pitch above max but acc_x safe -> no alarm."""
    sample = make_sample(pitch_reading=15, acc_x=ACC_X_SAFE)

    result = FlightEnvelopeChecker().check(sample)

    assert result.alarms is None or ALARM not in result.alarms


def test_low_pitch_alarms_when_acc_x_in_danger_range():
    """Negative mirror: pitch below min + acc_x in danger range -> alarm."""
    sample = make_sample(pitch_reading=-15, acc_x=ACC_X_IN_DANGER_RANGE)

    result = FlightEnvelopeChecker().check(sample)

    assert result.alarms is not None
    assert ALARM in result.alarms


def test_low_pitch_does_not_alarm_when_acc_x_safe():
    """Negative mirror: pitch below min but acc_x safe -> no alarm.

    This is the case the operator-precedence bug got wrong: `a or b and c` parses
    as `a or (b and c)`, so a pitch-below-min reading (`a`) alarmed unconditionally,
    ignoring the acc_x danger-range check that the mirrored positive branch
    correctly applies. Against the buggy code this assertion fails because the
    alarm fires even though acc_x is outside the danger range.
    """
    sample = make_sample(pitch_reading=-15, acc_x=ACC_X_SAFE)

    result = FlightEnvelopeChecker().check(sample)

    assert result.alarms is None or ALARM not in result.alarms
