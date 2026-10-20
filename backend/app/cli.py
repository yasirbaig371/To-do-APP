import argparse
from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserRole


def create_admin(email: str, full_name: str) -> None:
    email = email.strip().lower()
    full_name = full_name.strip()
    if not email or not full_name:
        raise SystemExit("Email and full name must not be blank.")
    password = getpass("Admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm admin password: ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    with SessionLocal() as db:
        existing_admin = db.scalar(
            select(User.id).where(User.role == UserRole.ADMIN).limit(1)
        )
        if existing_admin is not None:
            raise SystemExit(
                "An administrator already exists; use the protected admin API."
            )
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("An account with this email already exists.")
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
    print(f"Administrator created: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlled To-Do API operations")
    subparsers = parser.add_subparsers(dest="command", required=True)
    admin_parser = subparsers.add_parser(
        "create-admin", help="Create an administrator using hidden password prompts"
    )
    admin_parser.add_argument("--email", required=True)
    admin_parser.add_argument("--full-name", required=True)
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.email, args.full_name)


if __name__ == "__main__":
    main()
