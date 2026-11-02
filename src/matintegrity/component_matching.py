"""Exact caller-label comparisons shared by component and piping profiles."""


def material_membership_findings(material_condition_id, allowed_ids):
    if material_condition_id is None:
        return ["material_condition_id"], []
    if material_condition_id not in allowed_ids:
        return [], ["material_condition_id"]
    return [], []


def required_attribute_findings(attributes, required_attributes):
    missing, mismatched = [], []
    for key, expected in required_attributes.items():
        value = attributes.get(key)
        if value is None:
            missing.append(f"attribute:{key}")
        elif value != expected:
            mismatched.append(f"attribute:{key}")
    return missing, mismatched
