from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

from depends import get_current_creator, get_current_user, get_organizations_service
from models.users import User
from schemas.organizations import (
    AssignedTrainingResponse,
    GeneratedAccountResponse,
    GenerateAccountsRequest,
    OrganizationCreate,
    OrganizationDetailResponse,
    OrganizationEmployeeBulkCreate,
    OrganizationEmployeeCreate,
    OrganizationEmployeeResponse,
    OrganizationListResponse,
    OrganizationUpdate,
    ProvisionAccountsRequest,
    ProvisionAccountsResponse,
)
from services.organizations_service import OrganizationsService

router = APIRouter(prefix="/organizations", tags=["Организации"])


@router.post("", response_model=OrganizationListResponse)
async def create_organization(
    data: OrganizationCreate,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.create_organization(data, user.id)


@router.get("", response_model=List[OrganizationListResponse])
async def list_organizations(
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.list_organizations(user.id)


@router.get("/assigned-trainings", response_model=List[AssignedTrainingResponse])
async def assigned_trainings(
    user: User = Depends(get_current_user),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.assigned_trainings_for_user(user.id)


@router.get("/{org_id}", response_model=OrganizationDetailResponse)
async def get_organization(
    org_id: int,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.get_organization(org_id, user.id)


@router.patch("/{org_id}", response_model=OrganizationDetailResponse)
async def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.update_organization(org_id, data, user.id)


@router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    await service.delete_organization(org_id, user.id)
    return {"detail": "Организация удалена"}


@router.post("/{org_id}/trainings/{training_uuid}", response_model=OrganizationDetailResponse)
async def add_training(
    org_id: int,
    training_uuid: UUID4,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.add_training(org_id, training_uuid, user.id)


@router.delete("/{org_id}/trainings/{training_uuid}", response_model=OrganizationDetailResponse)
async def remove_training(
    org_id: int,
    training_uuid: UUID4,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.remove_training(org_id, training_uuid, user.id)


@router.post("/{org_id}/employees", response_model=OrganizationEmployeeResponse)
async def add_employee(
    org_id: int,
    data: OrganizationEmployeeCreate,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.add_employee(org_id, data, user.id)


@router.post("/{org_id}/employees/bulk", response_model=List[OrganizationEmployeeResponse])
async def add_employees_bulk(
    org_id: int,
    data: OrganizationEmployeeBulkCreate,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.add_employees_bulk(org_id, data, user.id)


@router.delete("/{org_id}/employees")
async def delete_all_employees(
    org_id: int,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    count = await service.delete_all_employees(org_id, user.id)
    return {"detail": f"Удалено сотрудников: {count}"}


@router.delete("/{org_id}/employees/{employee_id}")
async def delete_employee(
    org_id: int,
    employee_id: int,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    await service.delete_employee(org_id, employee_id, user.id)
    return {"detail": "Сотрудник удалён"}


@router.post("/{org_id}/accounts/provision", response_model=ProvisionAccountsResponse)
async def provision_accounts(
    org_id: int,
    body: ProvisionAccountsRequest,
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.provision_accounts(org_id, user.id, body)


@router.post("/{org_id}/employees/generate-accounts", response_model=List[GeneratedAccountResponse])
async def generate_accounts(
    org_id: int,
    body: GenerateAccountsRequest,
    regenerate: bool = Query(False, description="Перегенерировать пароли для всех сотрудников"),
    user: User = Depends(get_current_creator),
    service: OrganizationsService = Depends(get_organizations_service),
):
    return await service.generate_accounts(
        org_id, user.id, regenerate=regenerate, ttl_days=body.ttl_days
    )
