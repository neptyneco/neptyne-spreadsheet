"""Create initial tables

Revision ID: d6dd0a9e6b57
Revises: 
Create Date: 2022-02-08 15:37:07.399816

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd6dd0a9e6b57'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tyne_owner',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('handle', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('handle')
    )
    op.create_table('organization',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tyne_owner_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('domain', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['tyne_owner_id'], ['tyne_owner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tyne',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('file_name', sa.Text(), nullable=True),
    sa.Column('tyne_owner_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('default_access', sa.Enum('VIEW', 'COMMENT', 'EDIT', name='accesslevel'), nullable=True),
    sa.ForeignKeyConstraint(['tyne_owner_id'], ['tyne_owner.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tyne_owner_id', 'file_name', name='_owner_file_name_uc')
    )
    op.create_index(op.f('ix_tyne_file_name'), 'tyne', ['file_name'], unique=False)
    op.create_index(op.f('ix_tyne_name'), 'tyne', ['name'], unique=False)
    op.create_table('user',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tyne_owner_id', sa.Integer(), nullable=True),
    sa.Column('firebase_uid', sa.Text(), nullable=True),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('email', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['tyne_owner_id'], ['tyne_owner.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('firebase_uid')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_table('email_share',
    sa.Column('tyne_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.Text(), nullable=False),
    sa.Column('access_level', sa.Enum('VIEW', 'COMMENT', 'EDIT', name='accesslevel'), nullable=True),
    sa.ForeignKeyConstraint(['tyne_id'], ['tyne.id'], ),
    sa.PrimaryKeyConstraint('tyne_id', 'email')
    )
    op.create_table('notebook',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tyne_id', sa.Integer(), nullable=True),
    sa.Column('contents', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['tyne_id'], ['tyne.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('share',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('tyne_id', sa.Integer(), nullable=False),
    sa.Column('access_level', sa.Enum('VIEW', 'COMMENT', 'EDIT', name='accesslevel'), nullable=True),
    sa.ForeignKeyConstraint(['tyne_id'], ['tyne.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'tyne_id')
    )
    op.create_table('sheet',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tyne_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['tyne_id'], ['tyne.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_org',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', 'GUEST', name='role'), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'organization_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_org')
    op.drop_table('sheet')
    op.drop_table('share')
    op.drop_table('notebook')
    op.drop_table('email_share')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_tyne_name'), table_name='tyne')
    op.drop_index(op.f('ix_tyne_file_name'), table_name='tyne')
    op.drop_table('tyne')
    op.drop_table('organization')
    op.drop_table('tyne_owner')
    # ### end Alembic commands ###
