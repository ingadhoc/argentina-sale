##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCreditNoteReference(TestArCommon):
    """La NC que nace de una orden de venta lleva en Referencia sus facturas de origen.

    Los comprobantes se crean directamente y se le pasan a _set_reversed_entry como hace el
    core (con todas las facturas de la orden), en lugar de facturar la orden: así el test no
    depende de la política de facturación ni del tipo de pedido que tenga configurada la base.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls._create_journal("preprinted")
        cls.partner = cls.res_partner_adhoc
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product_iva_21.id,
                            "product_uom_qty": 2.0,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        cls.origin_invoice = cls._invoice_from_order(post=True)
        assert cls.origin_invoice.name, "La factura de origen debería quedar numerada al validarse"

    @classmethod
    def _invoice_from_order(cls, move_type="out_invoice", post=False):
        """Comprobante de la orden: lo que lo liga a ella es la línea de venta, como en el flujo real."""
        invoice = cls._create_invoice(
            move_type=move_type,
            partner_id=cls.partner,
            journal_id=cls.journal,
            ref=False,
            invoice_line_ids=[cls._prepare_invoice_line(product_id=cls.product_iva_21, price_unit=100.0)],
        )
        invoice.invoice_line_ids.sale_line_ids = [Command.set(cls.order.order_line.ids)]
        if post:
            invoice.action_post()
        return invoice

    def test_reference_takes_origin_invoice(self):
        """Caso feliz: la NC referencia la factura de la que salió."""
        credit_note = self._invoice_from_order(move_type="out_refund")

        self.order.invoice_ids._set_reversed_entry(credit_note)

        self.assertEqual(credit_note.ref, self.origin_invoice.name)

    def test_reference_ignores_draft_invoices(self):
        """Ticket 126371: con una factura en borrador en la orden, la NC no debe romper."""
        draft_invoice = self._invoice_from_order()
        self.assertFalse(draft_invoice.name, "Una factura en borrador no tiene número asignado")
        credit_note = self._invoice_from_order(move_type="out_refund")

        self.order.invoice_ids._set_reversed_entry(credit_note)

        self.assertEqual(
            credit_note.ref,
            self.origin_invoice.name,
            "Solo las facturas numeradas sirven como referencia",
        )

    def test_reference_empty_without_numbered_invoices(self):
        """Si ninguna factura de origen tiene número, la NC queda sin referencia en vez de fallar."""
        draft_invoice = self._invoice_from_order()
        credit_note = self._invoice_from_order(move_type="out_refund")

        draft_invoice._set_reversed_entry(credit_note)

        self.assertFalse(credit_note.ref)
