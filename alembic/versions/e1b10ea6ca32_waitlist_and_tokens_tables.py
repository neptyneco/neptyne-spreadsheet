"""Waitlist and tokens tables

Revision ID: e1b10ea6ca32
Revises: 8c6249e9aac2
Create Date: 2022-09-23 11:37:33.425946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1b10ea6ca32'
down_revision = '8c6249e9aac2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invite_tokens',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('token', sa.Text(), nullable=True),
    sa.Column('used_by_firebase_uid', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invite_tokens_token'), 'invite_tokens', ['token'], unique=False)
    op.create_table('waitlist',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('firebase_uid', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('hidden', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('firebase_uid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('waitlist')
    op.drop_index(op.f('ix_invite_tokens_token'), table_name='invite_tokens')
    op.drop_table('invite_tokens')
    # ### end Alembic commands ###
