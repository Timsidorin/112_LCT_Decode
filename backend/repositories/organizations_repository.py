from typing import List, Optional
from uuid import UUID

from pydantic import UUID4
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.organizations import Organization, OrganizationEmployee, organization_trainings
from models.trainings import Training, TrainingPublication


class OrganizationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, org: Organization) -> Organization:
        self.session.add(org)
        await self.session.flush()
        await self.session.refresh(org)
        return org

    async def get_by_id(self, org_id: int) -> Optional[Organization]:
        query = (
            select(Organization)
            .options(
                selectinload(Organization.trainings).selectinload(Training.publications),
                selectinload(Organization.employees),
            )
            .where(Organization.id == org_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: int) -> List[Organization]:
        query = (
            select(Organization)
            .options(
                selectinload(Organization.trainings).selectinload(Training.publications),
                selectinload(Organization.employees),
            )
            .where(Organization.owner_id == owner_id)
            .order_by(Organization.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, org_id: int) -> bool:
        org = await self.session.get(Organization, org_id)
        if not org:
            return False
        await self.session.delete(org)
        await self.session.flush()
        return True

    async def add_training(self, org_id: int, training_uuid: UUID4) -> bool:
        org = await self.get_by_id(org_id)
        if not org:
            return False
        training = await self.session.get(Training, training_uuid)
        if not training:
            return False
        if training not in org.trainings:
            org.trainings.append(training)
            await self.session.flush()
        return True

    async def remove_training(self, org_id: int, training_uuid: UUID4) -> bool:
        await self.session.execute(
            delete(organization_trainings).where(
                organization_trainings.c.organization_id == org_id,
                organization_trainings.c.training_uuid == training_uuid,
            )
        )
        await self.session.flush()
        return True

    async def add_employees_bulk(
        self, org_id: int, rows: List[dict]
    ) -> List[OrganizationEmployee]:
        created = []
        for row in rows:
            emp = OrganizationEmployee(organization_id=org_id, **row)
            self.session.add(emp)
            created.append(emp)
        await self.session.flush()
        for emp in created:
            await self.session.refresh(emp)
        return created

    async def get_employee(self, org_id: int, employee_id: int) -> Optional[OrganizationEmployee]:
        query = select(OrganizationEmployee).where(
            OrganizationEmployee.id == employee_id,
            OrganizationEmployee.organization_id == org_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete_employee(self, org_id: int, employee_id: int) -> bool:
        emp = await self.get_employee(org_id, employee_id)
        if not emp:
            return False
        await self.session.delete(emp)
        await self.session.flush()
        return True

    async def delete_all_employees(self, org_id: int) -> tuple[int, list[int]]:
        employees = await self.list_employees(org_id)
        if not employees:
            return 0, []
        user_ids = [e.user_id for e in employees if e.user_id]
        await self.session.execute(
            delete(OrganizationEmployee).where(
                OrganizationEmployee.organization_id == org_id
            )
        )
        await self.session.flush()
        return len(employees), user_ids

    async def employees_pending_accounts(self, org_id: int) -> List[OrganizationEmployee]:
        query = select(OrganizationEmployee).where(
            OrganizationEmployee.organization_id == org_id,
            OrganizationEmployee.account_generated.is_(False),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_employees(self, org_id: int) -> List[OrganizationEmployee]:
        query = select(OrganizationEmployee).where(
            OrganizationEmployee.organization_id == org_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_employee_by_provision_ref(
        self, org_id: int, provision_ref
    ) -> Optional[OrganizationEmployee]:
        query = select(OrganizationEmployee).where(
            OrganizationEmployee.organization_id == org_id,
            OrganizationEmployee.provision_ref == provision_ref,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_provision_slot(self, org_id: int, provision_ref) -> OrganizationEmployee:
        placeholder = f"slot-{str(provision_ref).split('-')[0]}"
        emp = OrganizationEmployee(
            organization_id=org_id,
            provision_ref=provision_ref,
            email=f"{placeholder}@accounts.local",
            full_name="Сотрудник",
            account_generated=False,
        )
        self.session.add(emp)
        await self.session.flush()
        return emp

    async def get_assigned_trainings_for_user(self, user_id: int) -> List[tuple]:
        query = (
            select(Organization, Training)
            .join(OrganizationEmployee, OrganizationEmployee.organization_id == Organization.id)
            .join(organization_trainings, organization_trainings.c.organization_id == Organization.id)
            .join(Training, Training.uuid == organization_trainings.c.training_uuid)
            .where(OrganizationEmployee.user_id == user_id)
            .distinct()
        )
        result = await self.session.execute(query)
        return list(result.all())

    async def get_active_publication(self, training_uuid: UUID) -> Optional[TrainingPublication]:
        query = (
            select(TrainingPublication)
            .where(
                TrainingPublication.training_uuid == training_uuid,
                TrainingPublication.is_active.is_(True),
            )
            .order_by(TrainingPublication.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_employees(self, org_id: int) -> int:
        query = select(func.count()).select_from(OrganizationEmployee).where(
            OrganizationEmployee.organization_id == org_id
        )
        result = await self.session.execute(query)
        return int(result.scalar() or 0)
