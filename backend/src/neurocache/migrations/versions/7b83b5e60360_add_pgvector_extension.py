"""add pgvector extension

Revision ID: 7b83b5e60360
Revises: f99f8b81c0bc
Create Date: 2026-01-23 16:14:49.859060

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "7b83b5e60360"
down_revision = "f99f8b81c0bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
