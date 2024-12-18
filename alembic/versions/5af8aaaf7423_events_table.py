"""events table

Revision ID: 5af8aaaf7423
Revises: 417e02512841
Create Date: 2022-11-03 09:30:37.329457

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5af8aaaf7423'
down_revision = '417e02512841'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tyne_event',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tyne_id', sa.Integer(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('severity', sa.Text(), nullable=True),
    sa.Column('extra', sa.JSON(), nullable=True),
    sa.Column('created', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['tyne_id'], ['tyne.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tyne_event')
    # ### end Alembic commands ###
