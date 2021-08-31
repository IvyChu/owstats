"""empty message

Revision ID: 17f40e419123
Revises: 
Create Date: 2021-08-24 22:08:32.333245

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17f40e419123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comp_stats', sa.Column('season', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('etime', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'etime')
    op.drop_column('comp_stats', 'season')
    # ### end Alembic commands ###