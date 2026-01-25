"""change knowledge source id to uuid

Revision ID: 22a499764c49
Revises: d4bb291acb34
Create Date: 2026-01-25 19:12:08.579828

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "22a499764c49"
down_revision = "d4bb291acb34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop foreign key constraint first (required before changing column types)
    op.drop_constraint("documents_knowledge_source_id_fkey", "documents", type_="foreignkey")

    # Drop the index before changing column types
    op.drop_index(op.f("ix_knowledge_sources_id"), table_name="knowledge_sources")

    # Change both columns to UUID type
    op.execute("ALTER TABLE knowledge_sources ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE documents ALTER COLUMN knowledge_source_id TYPE UUID USING knowledge_source_id::uuid")

    # Recreate the foreign key constraint
    op.create_foreign_key(
        "documents_knowledge_source_id_fkey",
        "documents",
        "knowledge_sources",
        ["knowledge_source_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Drop foreign key constraint first
    op.drop_constraint("documents_knowledge_source_id_fkey", "documents", type_="foreignkey")

    # Change both columns back to VARCHAR
    op.execute("ALTER TABLE documents ALTER COLUMN knowledge_source_id TYPE VARCHAR USING knowledge_source_id::text")
    op.execute("ALTER TABLE knowledge_sources ALTER COLUMN id TYPE VARCHAR USING id::text")

    # Recreate the foreign key constraint
    op.create_foreign_key(
        "documents_knowledge_source_id_fkey",
        "documents",
        "knowledge_sources",
        ["knowledge_source_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Recreate the index
    op.create_index(op.f("ix_knowledge_sources_id"), "knowledge_sources", ["id"], unique=False)
