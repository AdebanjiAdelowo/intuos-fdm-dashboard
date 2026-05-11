from logic.position_assignment import PositionAssigner

position_assigner = PositionAssigner(
    model_file_path="logic/position_assignment_data/f1.pkl",
    label_names_file_path="logic/position_assignment_data/f1_class_names.json",
    features_file_path="logic/position_assignment_data/f1_selected_features.json",
)
