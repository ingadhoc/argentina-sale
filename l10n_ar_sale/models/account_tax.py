##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from collections import defaultdict
from itertools import combinations

from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _l10n_ar_get_perceptions_below_base_threshold(self, base_lines, company):
        """En una orden de venta confirmada se mantienen las percepciones con las que se
        calculó su impuesto guardado (`amount_tax`), que no cambia si después se modifica el
        umbral. Si ninguna combinación de percepciones da ese importe, o si ese importe se está
        recalculando (al confirmar o al cambiar las líneas), se usa el umbral vigente.
        """
        excluded_taxes = super()._l10n_ar_get_perceptions_below_base_threshold(base_lines, company)
        order = self._l10n_ar_get_base_lines_order(base_lines)
        if (
            not order
            or order.state != "sale"
            # while it is being computed, the stored amount reads as 0
            or self.env.is_protected(order._fields["amount_tax"], order)
        ):
            return excluded_taxes

        currency = order.currency_id
        tax_amounts = defaultdict(float)
        for base_line in base_lines:
            for tax_data in base_line["tax_details"]["taxes_data"]:
                tax_amounts[tax_data["tax"]] += tax_data["raw_tax_amount_currency"]
        tax_amounts = {tax: currency.round(amount) for tax, amount in tax_amounts.items()}
        perceptions = [tax for tax in tax_amounts if tax._l10n_ar_is_perception()]
        candidates = [excluded_taxes] + [
            set(excluded) for size in range(len(perceptions) + 1) for excluded in combinations(perceptions, size)
        ]
        return next(
            (
                excluded
                for excluded in candidates
                if currency.compare_amounts(
                    sum(amount for tax, amount in tax_amounts.items() if tax not in excluded), order.amount_tax
                )
                == 0
            ),
            excluded_taxes,
        )

    @api.model
    def _l10n_ar_get_base_lines_order(self, base_lines):
        """Orden de venta guardada de las líneas base, si son todas de una misma orden.

        Mientras se edita en el formulario la orden es un registro nuevo: el estado y el
        impuesto guardado se leen de la orden guardada.
        """
        records = [base_line.get("record") for base_line in base_lines]
        order_lines = [
            record for record in records if isinstance(record, models.BaseModel) and record._name == "sale.order.line"
        ]
        if not order_lines:
            return None
        order = self.env["sale.order.line"].union(*order_lines).order_id
        # Early payment discount lines carry the order itself as record.
        if len(order) != 1 or any(
            not isinstance(record, models.BaseModel) or (record._name != "sale.order.line" and record != order)
            for record in records
        ):
            return None
        return order._origin or None
