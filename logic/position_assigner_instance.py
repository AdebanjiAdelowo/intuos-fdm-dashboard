from pathlib import Path
from logic.position_assignment import PositionAssigner

_DATA = Path(__file__).parent / "position_assignment_data"

position_assigner = PositionAssigner(
    model_file_path=str(_DATA / "f1.pkl"),
    label_names_file_path=str(_DATA / "f1_class_names.json"),
    features_file_path=str(_DATA / "f1_selected_features.json"),
)
