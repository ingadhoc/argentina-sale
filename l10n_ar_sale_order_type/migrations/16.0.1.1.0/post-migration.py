from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env['sale.order.type'].search([('sequence_id', '!=', False), ('sale_checkbook_id', '!=', False)]).write({'sale_checkbook_id': False})
