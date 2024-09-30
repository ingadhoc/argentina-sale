from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute("""
        UPDATE sale_order_type SET sale_checkbook_id = NULL
        WHERE sequence_id is not null
        AND sale_checkbook_id is not null
        """)
