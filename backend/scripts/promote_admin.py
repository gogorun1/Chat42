"""One-off script to bootstrap the first admin account.

Every signup defaults to role=user, and the `PATCH /admin/users/{id}/role`
endpoint requires an existing admin caller -- so the very first admin has
to be created some other way. This writes the role directly to the
database, bypassing the API.

Usage:
    docker compose exec backend python scripts/promote_admin.py <email>
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.user import User, UserRole


async def promote(email: str) -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            print(f"No user found with email {email!r}", file=sys.stderr)
            sys.exit(1)

        user.role = UserRole.ADMIN
        await db.commit()
        print(f"{email} is now {user.role.value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", help="Email of the user to promote to admin")
    args = parser.parse_args()
    asyncio.run(promote(args.email))


if __name__ == "__main__":
    main()
