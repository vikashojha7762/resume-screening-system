"""Seed initial admin user

Revision ID: 002_seed_admin
Revises: 001_initial
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String
from passlib.context import CryptContext
import uuid

# revision identifiers, used by Alembic.
revision = '002_seed_admin'
down_revision = '001_initial'
branch_labels = None
depends_on = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Create a table object for the users table
    users_table = table(
        'users',
        column('id', sa.UUID),
        column('email', String),
        column('hashed_password', String),
        column('is_active', sa.Boolean),
        column('is_superuser', sa.Boolean),
    )
    
    # Default admin credentials (should be changed in production)
    admin_email = "admin@resumescreening.com"
    admin_password = "admin123"  # Change this in production!
    hashed_password = pwd_context.hash(admin_password)
    
    # Check if admin user already exists
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM users WHERE email = :email"), {"email": admin_email})
    count = result.scalar()
    
    if count == 0:
        # Insert admin user
        op.bulk_insert(
            users_table,
            [{
                'id': uuid.uuid4(),
                'email': admin_email,
                'hashed_password': hashed_password,
                'is_active': True,
                'is_superuser': True,
            }]
        )
        print(f"✅ Admin user created: {admin_email} / {admin_password}")
    else:
        print(f"ℹ️  Admin user already exists: {admin_email}")


def downgrade() -> None:
    # Remove admin user
    op.execute("DELETE FROM users WHERE email = 'admin@resumescreening.com'")

