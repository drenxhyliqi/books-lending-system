"""add book description and embedding

Revision ID: 28c336120448
Revises: 0113d3ddf53f
Create Date: 2026-11-12 14:51:15.835511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '28c336120448'
down_revision: Union[str, Sequence[str], None] = '0113d3ddf53f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tipi vector nuk ekziston ne Postgres pa kete extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column('books', sa.Column('description', sa.Text(), nullable=True))
    # 1536 = gjatesia e vektorit qe e kthen text-embedding-3-small
    op.add_column('books', sa.Column('embedding', Vector(1536), nullable=True))

    # HNSW e gjen librin me te afert pa e krahasu pyetjen me secilin rresht
    # vector_cosine_ops = indeksi ndertohet per distancen kosinus
    op.create_index(
        'ix_books_embedding',
        'books',
        ['embedding'],
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_books_embedding', table_name='books')
    op.drop_column('books', 'embedding')
    op.drop_column('books', 'description')
    op.execute("DROP EXTENSION IF EXISTS vector")
