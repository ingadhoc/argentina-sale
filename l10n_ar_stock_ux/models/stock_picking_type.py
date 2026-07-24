from odoo import _, api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    _L10N_AR_SHARED_SEQUENCE_FIELDS = (
        "l10n_ar_cai_authorization_code",
        "l10n_ar_cai_expiration_date",
        "l10n_ar_sequence_number_start",
        "l10n_ar_sequence_number_end",
    )

    report_partner_id = fields.Many2one(
        "res.partner",
        string="Contacto para Encabezado",
        help="Para el encabezado de los remitos/comprobantes de entrega, la información a utilizar se obtendrá del "
        "primer datos definido de estos lugares:\n"
        "* Este campo\n"
        "* Dirección del Almacen de la transferencia\n"
        "* Información de la compañía de la transferencia",
    )
    report_signature_section = fields.Boolean(
        string="Añadir sección firma",
        help="Agregar al reporte una sección para añadir firma de confirmación de recepción.",
        default=False,
    )
    auto_assign_delivery_guide = fields.Boolean(
        string="Auto Assign Delivery Guide Number",
        help="Al validar una transferencia de este tipo, se asignará automáticamente un número de remito.",
        default=False,
    )

    @api.onchange("l10n_ar_sequence_number_start")
    def _add_padding_to_sequence_number_start(self):
        if self.l10n_ar_sequence_number_start:
            self.l10n_ar_sequence_number_start = self.l10n_ar_sequence_number_start.zfill(8)

    @api.onchange("l10n_ar_sequence_number_end")
    def _add_padding_to_sequence_number_end(self):
        if self.l10n_ar_sequence_number_end:
            self.l10n_ar_sequence_number_end = self.l10n_ar_sequence_number_end.zfill(8)

    @api.onchange("l10n_ar_delivery_sequence_prefix", "l10n_ar_next_delivery_number")
    def _onchange_l10n_ar_warn_shared_sequence(self):
        """Aviso no bloqueante: este picking type ya comparte l10n_ar_sequence_id con otros
        (por auto-match o asignación manual). Prefijo y próximo número viven en el registro
        ir.sequence subyacente, así que tocarlos acá también afecta a esos otros picking types
        (Clarificación 5 de la spec). El CAI, su vencimiento y el rango se sincronizan aparte
        vía write() (ver _L10N_AR_SHARED_SEQUENCE_FIELDS).
        """
        if not self.l10n_ar_sequence_id:
            return
        other_picking_types = self.search(
            [
                ("id", "!=", self._origin.id),
                ("l10n_ar_sequence_id", "=", self.l10n_ar_sequence_id.id),
            ]
        )
        if other_picking_types:
            return {
                "warning": {
                    "title": _("Shared delivery guide sequence"),
                    "message": _(
                        "The prefix and next number of this delivery guide sequence are also used by "
                        "these operation types: %s. Changing them here will affect them too."
                    )
                    % ", ".join(other_picking_types.mapped("display_name")),
                }
            }

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("l10n_ar_stock_ux_skip_shared_sequence_sync"):
            return res
        shared_vals = {field: vals[field] for field in self._L10N_AR_SHARED_SEQUENCE_FIELDS if field in vals}
        if not shared_vals:
            return res
        for picking_type in self:
            others = picking_type._l10n_ar_stock_ux_shared_sequence_picking_types()
            if others:
                others.with_context(l10n_ar_stock_ux_skip_shared_sequence_sync=True).write(shared_vals)
        return res

    def _l10n_ar_stock_ux_shared_sequence_picking_types(self):
        """Otros picking types que comparten l10n_ar_sequence_id con este (mismo CAI/talonario)."""
        self.ensure_one()
        if not self.l10n_ar_sequence_id:
            return self.browse()
        return self.search(
            [
                ("id", "!=", self.id),
                ("l10n_ar_sequence_id", "=", self.l10n_ar_sequence_id.id),
            ]
        )

    def _ensure_l10n_ar_stock_sequence(self):
        to_create = self.browse()
        for picking_type in self:
            if picking_type.l10n_ar_sequence_id:
                continue
            if not picking_type.l10n_ar_document_type_id:
                # Sin tipo de documento todavía no hay remito que numerar: no crear
                # secuencia. Si se crea acá (p.ej. por el default de
                # l10n_ar_delivery_sequence_prefix al hacer create() sin datos AR),
                # esa secuencia "placeholder" bloquea el auto-match de más abajo el día
                # que el picking type se configure de verdad con un documento AR.
                continue
            shared_sequence = picking_type._l10n_ar_stock_ux_find_shared_sequence()
            if shared_sequence:
                picking_type.l10n_ar_sequence_id = shared_sequence
            else:
                to_create += picking_type
        if to_create:
            super(StockPickingType, to_create)._ensure_l10n_ar_stock_sequence()

    def _l10n_ar_stock_ux_find_shared_sequence(self):
        """Buscar una l10n_ar_sequence_id para reutilizar entre picking types que comparten
        el mismo tipo de documento y prefijo de secuencia (mismo CAI/talonario).

        Prioriza la propia compañía; solo si no hay match ahí busca en padre/hermanas que
        compartan CUIT, para no depender del orden no determinístico de mezclar ambos scopes
        en una sola query.
        """
        self.ensure_one()
        prefix = self.l10n_ar_delivery_sequence_prefix
        if not (prefix and self.l10n_ar_document_type_id):
            return self.env["ir.sequence"]
        base_domain = [
            ("id", "!=", self.id),
            ("l10n_ar_document_type_id", "=", self.l10n_ar_document_type_id.id),
            ("l10n_ar_sequence_id", "!=", False),
        ]
        own_company = self.search(base_domain + [("company_id", "=", self.company_id.id)])
        match = own_company.filtered(lambda pt: pt.l10n_ar_sequence_id.prefix == f"{prefix}-")[:1]
        if match:
            return match.l10n_ar_sequence_id
        if self.company_id.parent_id and self.company_id.vat:
            # El CAI es una autorización de ARCA atada a un CUIT, así que solo se puede
            # reutilizar la secuencia de otra compañía del árbol si comparte CUIT con esta
            # (branches de la misma entidad fiscal). Sin CUIT cargado no hay forma de
            # verificarlo, así que no se sale de la propia compañía: el usuario siempre puede
            # asignar l10n_ar_sequence_id a mano desde el modo debug.
            related = self.search(
                base_domain
                + [
                    ("company_id", "child_of", self.company_id.parent_id.id),
                    ("company_id.vat", "=", self.company_id.vat),
                ]
            )
            match = related.filtered(lambda pt: pt.l10n_ar_sequence_id.prefix == f"{prefix}-")[:1]
            if match:
                return match.l10n_ar_sequence_id
        return self.env["ir.sequence"]
