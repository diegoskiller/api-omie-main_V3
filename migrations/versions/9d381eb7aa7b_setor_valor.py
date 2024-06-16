"""setor valor

Revision ID: 9d381eb7aa7b
Revises: 8f40cbb1e9ca
Create Date: 2024-06-16 05:05:34.565223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d381eb7aa7b'
down_revision = '8f40cbb1e9ca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cadastro_itens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('setor', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('valor_unitario', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cadastro_itens', schema=None) as batch_op:
        batch_op.drop_column('valor_unitario')
        batch_op.drop_column('setor')

    # ### end Alembic commands ###
