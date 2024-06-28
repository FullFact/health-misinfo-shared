from pydantic import BaseModel, ValidationError


class LabelsModel(BaseModel):
    understandability: str
    type_of_claim: str
    type_of_medical_claim: str
    support: str
    harm: str


class ClaimModel(BaseModel):
    claim: str
    original_text: str
    labels: LabelsModel


def assert_output_json_format(output: dict) -> bool:
    try:
        ClaimModel(**output)
    except ValidationError:
        print(output)
        return False
    return True


def insert_missing_key_as_null(output: dict) -> dict:
    # fill in data if it is missing
    if "original_text" not in output.keys():
        output["original_text"] = "not found"
    labels = output.get("labels", {})
    # missing labels will be filled in as blank
    for k in list(LabelsModel.model_fields):
        if k not in labels.keys():
            labels[k] = ""
    output["labels"] = labels
    return output
