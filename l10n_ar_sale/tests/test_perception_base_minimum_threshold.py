##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
"""
Base mínima de percepciones (`l10n_ar_base_minimum_threshold`, ver l10n_ar_tax) en la
orden de venta: la orden confirmada mantiene las percepciones con las que se calculó su
impuesto guardado, aunque después cambie el umbral.

Casos (alícuota 3%, umbral 300000):
    1. Confirmada con percepción, después se sube el umbral → sigue la percepción.
    2. Confirmada sin percepción, después se baja el umbral → sigue sin percepción.
    3. En presupuesto se evalúa el umbral vigente.
    4. Como el 1, con un plazo de pago con descuento por pronto pago "mixed".
    5. Como el 1, editando una línea en el formulario → sigue la percepción.
    6. Confirmada, se sube el umbral, se cancela, se vuelve a presupuesto y se confirma
       de nuevo → se evalúa el umbral vigente.
    7. Al duplicar una orden confirmada, la copia evalúa el umbral vigente.
    8. Confirmada con percepción, se sube el umbral y después se cambia el precio → se
       recalcula con el umbral vigente.
"""

from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestPerceptionBaseMinimumThreshold(TestArCommon):
    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.env.ref("sales_team.group_sale_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # exception rules of other modules leave the order in draft on action_confirm
        if cls.env["sale.order"]._fields.get("ignore_exception"):
            cls.env["exception.rule"].sudo().search([("active", "=", True)]).write({"active": False})

        perception_group = cls.env.ref(
            "account.%i_ri_tax_percepcion_iibb_caba_aplicada" % cls.env.company.id
        ).tax_group_id
        cls.perception_tax = cls.env["account.tax"].create(
            {
                "name": "Test Percepción IIBB 3%",
                "amount": 3.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "country_id": cls.env.ref("base.ar").id,
                "company_id": cls.company_ri.id,
                "l10n_ar_state_id": cls.env.ref("base.state_ar_c").id,
                "tax_group_id": perception_group.id,
                "l10n_ar_base_minimum_threshold": 300000,
            }
        )

    def _order(self, price_unit, payment_term=None, confirm=True):
        """Orden con una línea con IVA 21% y la percepción, confirmada por defecto."""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.res_partner_adhoc.id,
                "company_id": self.company_ri.id,
                "payment_term_id": payment_term and payment_term.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.service_iva_21.id,
                            "product_uom_qty": 1,
                            "price_unit": price_unit,
                            "tax_ids": [Command.set((self.tax_21 + self.perception_tax).ids)],
                        }
                    )
                ],
            }
        )
        # compute the stored totals of the quotation, as at the end of the create request
        self.env.flush_all()
        if confirm:
            order.action_confirm()
            # the confirmation computes them again, as at the end of its request
            self.env.flush_all()
        return order

    def _assert_order_total(self, order, expected_total):
        # `tax_totals` is not stored: invalidate it to recompute with the current settings.
        order.invalidate_recordset(["tax_totals"])
        self.assertAlmostEqual(order.tax_totals["total_amount_currency"], expected_total, places=2)
        self.assertAlmostEqual(order.amount_total, expected_total, places=2)

    def test_01_confirmed_order_keeps_perception_when_threshold_raised(self):
        """Confirmada con percepción (301000 > 300000); se sube el umbral a 400000 → sigue
        la percepción: 301000 * 1.24 = 373240."""
        order = self._order(301000.0)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        self._assert_order_total(order, 373240.0)

    def test_02_confirmed_order_keeps_no_perception_when_threshold_lowered(self):
        """Confirmada sin percepción (299000 < 300000); se baja el umbral a 200000 → sigue
        sin percepción: 299000 * 1.21 = 361790."""
        order = self._order(299000.0)
        self.perception_tax.l10n_ar_base_minimum_threshold = 200000
        self._assert_order_total(order, 361790.0)

    def test_03_quotation_uses_current_threshold(self):
        """Presupuesto de 301000; se sube el umbral a 400000 → sin percepción: 364210."""
        order = self._order(301000.0, confirm=False)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        order.invalidate_recordset(["tax_totals"])
        self.assertAlmostEqual(order.tax_totals["total_amount_currency"], 364210.0, places=2)

    def test_04_mixed_early_payment_discount(self):
        """Como el 1, con descuento por pronto pago "mixed": el impuesto se calcula sobre la
        base con descuento (310000 * 0.98 = 303800 > umbral) y la orden suma líneas propias
        para eso. Se sube el umbral → el total no cambia."""
        payment_term = self.env["account.payment.term"].create(
            {
                "name": "Pronto pago 2% mixed",
                "company_id": self.company_ri.id,
                "early_discount": True,
                "discount_percentage": 2.0,
                "discount_days": 10,
                "early_pay_discount_computation": "mixed",
                "line_ids": [Command.create({"value": "percent", "value_amount": 100.0, "nb_days": 30})],
            }
        )
        order = self._order(310000.0, payment_term=payment_term)
        total = order.amount_total
        self.assertGreater(total, 310000.0 * 1.21)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        self._assert_order_total(order, total)

    def test_05_form_edition_keeps_perception(self):
        """Como el 1, editando una línea en el formulario: mientras se edita la orden es un
        registro nuevo y tiene que seguir mostrando la percepción, 373240."""
        order = self._order(301000.0)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.name = "Edited description"
            self.assertAlmostEqual(order_form.tax_totals["total_amount_currency"], 373240.0, places=2)

    def test_06_reconfirmed_order_uses_current_threshold(self):
        """Confirmada con percepción; se sube el umbral a 400000, se cancela, se vuelve a
        presupuesto y se confirma de nuevo → se evalúa el umbral vigente, sin percepción:
        364210."""
        order = self._order(301000.0)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        order._action_cancel()
        order.action_draft()
        order.invalidate_recordset(["tax_totals"])
        self.assertAlmostEqual(order.tax_totals["total_amount_currency"], 364210.0, places=2)
        order.action_confirm()
        self.env.flush_all()
        self._assert_order_total(order, 364210.0)

    def test_07_copy_uses_current_threshold(self):
        """Al duplicar una orden confirmada la copia es un presupuesto: con el umbral en
        400000 sale sin percepción, 364210."""
        order = self._order(301000.0)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        copy = order.copy()
        self._assert_order_total(copy, 364210.0)

    def test_08_price_change_uses_current_threshold(self):
        """Confirmada con percepción; se sube el umbral a 400000 y después se cambia el
        precio a 302000 → la orden se recalcula con el umbral vigente, sin percepción:
        302000 * 1.21 = 365420."""
        order = self._order(301000.0)
        self.perception_tax.l10n_ar_base_minimum_threshold = 400000
        order.order_line.price_unit = 302000.0
        self._assert_order_total(order, 365420.0)
