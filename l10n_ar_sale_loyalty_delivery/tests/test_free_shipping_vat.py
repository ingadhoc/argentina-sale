##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestFreeShippingVat(TestArCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # el usuario de AccountTestInvoicingCommon no tiene grupos de ventas, y los pedidos,
        # transportistas y programas de fidelización los administra Ventas/Administrador
        cls.env.user.group_ids += cls.env.ref("sales_team.group_sale_manager")

        cls.vat_21 = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company_ri.id),
                ("type_tax_use", "=", "sale"),
                ("tax_group_id.l10n_ar_vat_afip_code", "=", "5"),
            ],
            limit=1,
        )
        assert cls.vat_21, "No se encontró el IVA 21% de venta de la compañía de prueba"

        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Flete",
                "type": "service",
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
                "sale_ok": False,
                "purchase_ok": False,
                "list_price": 100.0,
                "taxes_id": [Command.set(cls.vat_21.ids)],
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Flete",
                "fixed_price": 100.0,
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
            }
        )
        cls.program = cls.env["loyalty.program"].create(
            {
                "name": "Envío gratis",
                "program_type": "promotion",
                "trigger": "auto",
                "applies_on": "current",
                "rule_ids": [Command.create({"minimum_amount": 0.0})],
                "reward_ids": [Command.create({"reward_type": "shipping"})],
            }
        )
        cls.reward = cls.program.reward_ids
        # el producto de la recompensa lo crea loyalty tomando los impuestos por defecto de
        # la compañía; lo fijamos para no depender de esa configuración en el test
        cls.reward.discount_line_product_id.taxes_id = [Command.set(cls.vat_21.ids)]

    def _new_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.res_partner_adhoc.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_iva_21.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 1000.0,
                            "tax_ids": [Command.set(self.vat_21.ids)],
                        }
                    )
                ],
            }
        )
        order._update_programs_and_rewards()
        return order

    def _claim_free_shipping(self, order):
        coupon = order.coupon_point_ids.coupon_id.filtered(lambda c: c.program_id == self.program)
        self.assertEqual(len(coupon), 1, "El programa de envío gratis debería aplicarse al pedido")
        status = order._apply_program_reward(self.reward, coupon)
        self.assertNotIn("error", status, "No se pudo reclamar la recompensa: %s" % status)
        return order.order_line.filtered(lambda line: line.reward_id.reward_type == "shipping")

    def _vat_taxes(self, line):
        return line.tax_ids.filtered(lambda tax: tax.tax_group_id.l10n_ar_vat_afip_code)

    def test_free_shipping_without_delivery_line(self):
        """Sin línea de flete, la recompensa debe nacer con un único IVA y sin bloquear el pedido."""
        order = self._new_order()
        reward_line = self._claim_free_shipping(order)

        self.assertTrue(reward_line, "Debería haberse agregado la línea de recompensa de envío gratis")
        self.assertEqual(len(self._vat_taxes(reward_line)), 1)
        self.assertEqual(reward_line.price_unit, 0.0, "Sin flete la recompensa vale 0, igual que en el estándar")
        self.assertEqual(reward_line.price_total, 0.0, "El IVA sobre base 0 no debe alterar importes")

    def test_free_shipping_with_delivery_line(self):
        """Con línea de flete se mantiene el comportamiento estándar: hereda el IVA del flete."""
        order = self._new_order()
        order.set_delivery_line(self.carrier, self.carrier.fixed_price)
        reward_line = self._claim_free_shipping(order)

        delivery_line = order.order_line.filtered("is_delivery")
        self.assertEqual(reward_line.tax_ids, delivery_line.tax_ids)
        self.assertEqual(reward_line.price_unit, -delivery_line.price_unit)

    def test_tax_ids_from_commands(self):
        """Los comandos x2many se resuelven a ids, sin depender de cómo los arme el estándar."""
        resolve = self.env["sale.order"]._l10n_ar_tax_ids_from_commands

        self.assertFalse(resolve(None))
        self.assertFalse(resolve([]))
        self.assertFalse(resolve([(Command.CLEAR, 0, 0)]))
        # forma que usa hoy sale_loyalty_delivery
        self.assertEqual(resolve([(Command.CLEAR, 0, 0), (Command.LINK, 7, False)]), {7})
        # forma alternativa: un único SET, que no trae ningún LINK
        self.assertEqual(resolve([Command.set([7, 9])]), {7, 9})
        # un SET posterior reemplaza lo anterior; UNLINK descuenta
        self.assertEqual(resolve([Command.link(9), Command.set([7])]), {7})
        self.assertFalse(resolve([Command.link(7), Command.unlink(7)]))

    def test_free_shipping_without_taxes_on_reward_product(self):
        """Si el producto de la recompensa no tiene impuestos, se usa el de venta de la compañía."""
        self.reward.discount_line_product_id.taxes_id = [Command.clear()]
        self.company_ri.account_sale_tax_id = self.vat_21

        order = self._new_order()
        reward_line = self._claim_free_shipping(order)

        self.assertEqual(self._vat_taxes(reward_line), self.vat_21)

    def test_free_shipping_after_removing_delivery_line(self):
        """Al quitar el transportista la recompensa se recalcula y no debe quedar sin IVA."""
        order = self._new_order()
        order.set_delivery_line(self.carrier, self.carrier.fixed_price)
        self._claim_free_shipping(order)

        order._remove_delivery_line()
        order._update_programs_and_rewards()

        reward_line = order.order_line.filtered(lambda line: line.reward_id.reward_type == "shipping")
        self.assertEqual(len(self._vat_taxes(reward_line)), 1)
