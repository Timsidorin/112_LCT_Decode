from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)


class OrganizationTrainingBrief(BaseModel):
    uuid: UUID
    title: str
    publish: bool
    public_link: Optional[str] = None

    model_config = {"from_attributes": True}


class OrganizationEmployeeCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    position: Optional[str] = Field(None, max_length=150)


class OrganizationEmployeeBulkCreate(BaseModel):
    employees: List[OrganizationEmployeeCreate]


class OrganizationEmployeeResponse(BaseModel):
    id: int
    email: str
    full_name: str
    position: Optional[str] = None
    user_id: Optional[int] = None
    account_generated: bool
    account_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    employees_count: int = 0
    trainings_count: int = 0

    model_config = {"from_attributes": True}


class OrganizationDetailResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    trainings: List[OrganizationTrainingBrief] = Field(default_factory=list)
    employees: List[OrganizationEmployeeResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class GeneratedAccountResponse(BaseModel):
    employee_id: int
    email: str
    full_name: str
    temp_password: str
    account_expires_at: datetime
    ttl_days: int


class GenerateAccountsRequest(BaseModel):
    ttl_days: int = Field(..., ge=1, le=365, description="Срок действия учётных записей в днях")


class ProvisionSlotRequest(BaseModel):
    provision_ref: UUID


class ProvisionAccountsRequest(BaseModel):
    ttl_days: int = Field(..., ge=1, le=365)
    slots: List[ProvisionSlotRequest] = Field(..., min_length=1)


class ProvisionedAccountResponse(BaseModel):
    provision_ref: UUID
    slot_id: int
    login_id: str
    temp_password: str
    user_id: int
    account_expires_at: datetime
    ttl_days: int


class ProvisionAccountsResponse(BaseModel):
    accounts: List[ProvisionedAccountResponse]


class AssignedTrainingResponse(BaseModel):
    organization_id: int
    organization_name: str
    training_uuid: UUID
    title: str
    public_link: Optional[str] = None
