"""empty message

Revision ID: 00872d243cdc
Revises: fd77d0a3e624
Create Date: 2021-08-30 14:14:27.055689

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00872d243cdc'
down_revision = 'fd77d0a3e624'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('system', sa.String(length=16), nullable=True),
    sa.Column('system_id', sa.String(length=100), nullable=True),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.Column('amount', sa.BigInteger(), nullable=True),
    sa.Column('reason', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('performed_at', sa.DateTime(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    # ### end Alembic commands ###