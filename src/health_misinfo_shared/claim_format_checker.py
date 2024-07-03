from pydantic import BaseModel


class StrictLabelsModel(BaseModel):
    understandability: str
    type_of_claim: str
    type_of_medical_claim: str
    support: str
    harm: str


class StrictClaimModel(BaseModel):
    claim: str
    original_text: str
    labels: StrictLabelsModel


class LabelsModel(BaseModel):
    understandability: str = ""
    type_of_claim: str = ""
    type_of_medical_claim: str = ""
    support: str = ""
    harm: str = ""


class ClaimModel(BaseModel):
    claim: str
    original_text: str = "not found"
    labels: LabelsModel = LabelsModel()
