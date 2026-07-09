from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.organizations import OrganizationEmployee
from models.users import User, UserRole
from repositories.users_repository import UserRepository


def temp_account_expires_at(
    *, ttl_days: int, from_dt: Optional[datetime] = None
) -> datetime:
    base = from_dt or datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return base + timedelta(days=ttl_days)


def is_account_expired(
    expires_at: Optional[datetime], *, now: Optional[datetime] = None
) -> bool:
    if expires_at is None:
        return False
    current = now or datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return current >= expires_at


class TempEmployeeAccountsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users_repo = UserRepository(session)

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        query = select(User.id).where(
            User.role == UserRole.EMPLOYEE,
            User.expires_at.isnot(None),
            User.expires_at <= now,
        )
        result = await self.session.execute(query)
        user_ids = [row[0] for row in result.all()]
        if not user_ids:
            return 0

        removed = 0
        for user_id in user_ids:
            if await self._remove_expired_user(user_id):
                removed += 1
        await self.session.commit()
        return removed

    async def cleanup_user_if_expired(self, user: User) -> bool:
        if user.role != UserRole.EMPLOYEE or not is_account_expired(user.expires_at):
            return False
        ok = await self._remove_expired_user(user.id)
        if ok:
            await self.session.commit()
        return ok

    async def _remove_expired_user(self, user_id: int) -> bool:
        user = await self.users_repo.get_by_id(user_id)
        if not user:
            return False
        if user.role != UserRole.EMPLOYEE or not is_account_expired(user.expires_at):
            return False

        await self.session.execute(
            update(OrganizationEmployee)
            .where(OrganizationEmployee.user_id == user_id)
            .values(
                user_id=None,
                account_generated=False,
                account_expires_at=None,
            )
        )
        await self.session.delete(user)
        await self.session.flush()
        return True
