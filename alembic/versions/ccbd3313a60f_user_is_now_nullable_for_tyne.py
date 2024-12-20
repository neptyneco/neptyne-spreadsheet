"""User is now nullable for tyne

Revision ID: ccbd3313a60f
Revises: add549685881
Create Date: 2023-09-07 16:57:27.244608

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ccbd3313a60f'
down_revision = 'add549685881'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tyne', 'tyne_owner_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.add_column('user', sa.Column('firebase_app', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'firebase_app')
    op.alter_column('tyne', 'tyne_owner_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
