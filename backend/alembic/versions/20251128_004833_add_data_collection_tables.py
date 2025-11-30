"""add data collection tables

Revision ID: 20251128_004833
Revises:
Create Date: 2025-11-28 00:48:33

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251128_004833'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ip_whitelist table
    op.create_table(
        'ip_whitelist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip_address')
    )
    op.create_index(op.f('ix_ip_whitelist_id'), 'ip_whitelist', ['id'], unique=False)
    op.create_index(op.f('ix_ip_whitelist_ip_address'), 'ip_whitelist', ['ip_address'], unique=True)
    op.create_index(op.f('ix_ip_whitelist_is_active'), 'ip_whitelist', ['is_active'], unique=False)

    # Create data_source_config table
    op.create_table(
        'data_source_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_params', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_name')
    )
    op.create_index(op.f('ix_data_source_config_id'), 'data_source_config', ['id'], unique=False)
    op.create_index(op.f('ix_data_source_config_source_name'), 'data_source_config', ['source_name'], unique=True)

    # Create traffic_data table (main table)
    op.create_table(
        'traffic_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('batch_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_traffic_data_id'), 'traffic_data', ['id'], unique=False)
    op.create_index(op.f('ix_traffic_data_batch_id'), 'traffic_data', ['batch_id'], unique=False)

    # Create threat_predictions table
    op.create_table(
        'threat_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('traffic_data_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('prediction_score', sa.Float(), nullable=False),
        sa.Column('is_attack', sa.Boolean(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=True, server_default=sa.text('0.5')),
        sa.Column('model_version', sa.String(), nullable=True, server_default=sa.text("'ensemble_v1'")),
        sa.ForeignKeyConstraint(['traffic_data_id'], ['traffic_data.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('traffic_data_id')
    )
    op.create_index(op.f('ix_threat_predictions_id'), 'threat_predictions', ['id'], unique=False)

    # Create attack_predictions table
    op.create_table(
        'attack_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('traffic_data_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('attack_type_encoded', sa.Integer(), nullable=False),
        sa.Column('attack_type_name', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True, server_default=sa.text("'decision_tree_v1'")),
        sa.ForeignKeyConstraint(['traffic_data_id'], ['traffic_data.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('traffic_data_id')
    )
    op.create_index(op.f('ix_attack_predictions_id'), 'attack_predictions', ['id'], unique=False)

    # Create self_healing_actions table
    op.create_table(
        'self_healing_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attack_prediction_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('action_description', sa.Text(), nullable=False),
        sa.Column('action_params', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default=sa.text("'logged'")),
        sa.Column('execution_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['attack_prediction_id'], ['attack_predictions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attack_prediction_id')
    )
    op.create_index(op.f('ix_self_healing_actions_id'), 'self_healing_actions', ['id'], unique=False)

    # Insert default data source configurations
    op.execute("""
        INSERT INTO data_source_config (source_name, description, is_enabled, config_params)
        VALUES
            ('packet_capture', 'Network packet capture from server interface', false, '{"interface": "any", "buffer_size": 1000}'),
            ('external_kafka', 'External data providers via Kafka', false, '{"topic": "external-traffic"}'),
            ('internal_kafka', 'Internal test data stream', true, '{"topic": "network-traffic"}')
    """)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_index(op.f('ix_self_healing_actions_id'), table_name='self_healing_actions')
    op.drop_table('self_healing_actions')

    op.drop_index(op.f('ix_attack_predictions_id'), table_name='attack_predictions')
    op.drop_table('attack_predictions')

    op.drop_index(op.f('ix_threat_predictions_id'), table_name='threat_predictions')
    op.drop_table('threat_predictions')

    op.drop_index(op.f('ix_traffic_data_batch_id'), table_name='traffic_data')
    op.drop_index(op.f('ix_traffic_data_id'), table_name='traffic_data')
    op.drop_table('traffic_data')

    op.drop_index(op.f('ix_data_source_config_source_name'), table_name='data_source_config')
    op.drop_index(op.f('ix_data_source_config_id'), table_name='data_source_config')
    op.drop_table('data_source_config')

    op.drop_index(op.f('ix_ip_whitelist_is_active'), table_name='ip_whitelist')
    op.drop_index(op.f('ix_ip_whitelist_ip_address'), table_name='ip_whitelist')
    op.drop_index(op.f('ix_ip_whitelist_id'), table_name='ip_whitelist')
    op.drop_table('ip_whitelist')
