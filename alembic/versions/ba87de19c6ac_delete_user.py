"""Delete user

Revision ID: ba87de19c6ac
Revises: 3d16745af53c
Create Date: 2024-09-17 09:05:56.592109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba87de19c6ac'
down_revision = '3d16745af53c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('firebase_user_user_id_fkey', 'firebase_user', type_='foreignkey')
    op.create_foreign_key('firebase_user_user_id_fkey', 'firebase_user', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.alter_column('function_call_cache', 'combined_hash',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)
    op.drop_constraint('tyne_secrets_user_id_fkey', 'tyne_secrets', type_='foreignkey')
    op.create_foreign_key('tyne_secrets_user_id_fkey', 'tyne_secrets', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('tyne_secrets_user_id_fkey', 'tyne_secrets', type_='foreignkey')
    op.create_foreign_key('tyne_secrets_user_id_fkey', 'tyne_secrets', 'user', ['user_id'], ['id'])
    op.alter_column('function_call_cache', 'combined_hash',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
    op.drop_constraint('firebase_user_user_id_fkey', 'firebase_user', type_='foreignkey')
    op.create_foreign_key('firebase_user_user_id_fkey', 'firebase_user', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###
