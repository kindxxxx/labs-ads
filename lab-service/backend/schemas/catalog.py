from __future__ import annotations

from pydantic import BaseModel


class LanguageOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class LabOut(BaseModel):
    id: int
    subject: str
    lab_number: int
    price: int
    description: str
    requirements: str
    languages: list[LanguageOut]

    model_config = {"from_attributes": True}


class SubjectOut(BaseModel):
    code: str
    label: str
