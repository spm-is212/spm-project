from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    collaborator_ids: List[str] = Field(default_factory=list, description="List of user UUIDs who are collaborators")

class ProjectCreate(ProjectBase):
    collaborator_ids: List[str] = Field(..., min_length=1, description="List of user UUIDs who are collaborators")

    @field_validator("collaborator_ids")
    @classmethod
    def validate_collaborators(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("Project must have at least one collaborator")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    collaborator_ids: Optional[List[str]] = Field(None, description="List of user UUIDs who are collaborators")

    @field_validator("collaborator_ids")
    @classmethod
    def validate_collaborators(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) == 0:
            raise ValueError("Project must have at least one collaborator")
        return v


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    collaborator_ids: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
