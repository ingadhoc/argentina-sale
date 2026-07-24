from lxml import etree
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.tests import tagged


@tagged("post_install_l10n", "post_install", "-at_install")
class TestL10nArStockUxSharedSequence(TestArCommon):
    """Tarea #71177: remito en traslado interno + secuencia compartida por CAI."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_remito = cls.env.ref("l10n_ar.dc_r_r")

    def _create_picking_type(self, company, code, sequence_code):
        return self.env["stock.picking.type"].create(
            {
                "name": f"Test {code} {sequence_code}",
                "code": code,
                "company_id": company.id,
                "sequence_code": sequence_code,
            }
        )

    def _create_child_company(self, name, vat):
        """Compañía hija de company_ri con su propio CUIT: el fallback de secuencia solo
        aplica entre compañías del árbol que comparten CUIT (misma entidad fiscal)."""
        company = self._create_company(
            name=name,
            parent_id=self.company_ri.id,
            l10n_ar_afip_start_date="2024-01-01",
            l10n_ar_gross_income_type="exempt",
        )
        company.partner_id.write(
            {
                "l10n_latam_identification_type_id": self.env.ref("l10n_ar.it_cuit").id,
                "vat": vat,
            }
        )
        return company

    def _configure_delivery_guide(self, picking_type, document_type, prefix, next_number=1):
        picking_type.write(
            {
                "l10n_ar_document_type_id": document_type.id,
                "l10n_ar_cai_authorization_code": "99999999999999",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_delivery_sequence_prefix": prefix,
                "l10n_ar_next_delivery_number": next_number,
            }
        )
        return picking_type

    def test_internal_picking_type_can_configure_delivery_guide(self):
        """Mejora 1: la vista no debe ocultar l10n_ar_document_type_id para code == 'internal'."""
        internal = self._create_picking_type(self.company_ri, "internal", "INT-VIEW")
        arch = etree.fromstring(internal.get_view()["arch"])
        field_node = arch.find('.//field[@name="l10n_ar_document_type_id"]')
        self.assertIsNotNone(field_node, "No se encontró el campo l10n_ar_document_type_id en la vista.")
        self.assertIn("internal", field_node.get("invisible") or "")

    def test_shared_sequence_same_company_same_prefix(self):
        """Mejora 2, caso feliz: mismo documento + mismo prefijo en la misma compañía -> misma secuencia."""
        outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-TEST")
        internal = self._create_picking_type(self.company_ri, "internal", "INT-TEST")

        self._configure_delivery_guide(outgoing, self.document_type_remito, "00001")
        self.assertTrue(outgoing.l10n_ar_sequence_id)

        self._configure_delivery_guide(internal, self.document_type_remito, "00001")

        self.assertEqual(
            internal.l10n_ar_sequence_id,
            outgoing.l10n_ar_sequence_id,
            "Deberían compartir la misma secuencia por tener mismo documento y prefijo.",
        )

    def test_no_match_creates_new_sequence(self):
        """Regresión: sin match de documento/prefijo se sigue creando una secuencia nueva."""
        outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-TEST2")
        internal = self._create_picking_type(self.company_ri, "internal", "INT-TEST2")

        self._configure_delivery_guide(outgoing, self.document_type_remito, "00002")
        self._configure_delivery_guide(internal, self.document_type_remito, "00003")

        self.assertNotEqual(outgoing.l10n_ar_sequence_id, internal.l10n_ar_sequence_id)

    def test_shared_sequence_prioritizes_own_company_over_parent(self):
        """Clarificación 2: si hay match en la propia compañía y en el padre, gana la propia."""
        child_company = self._create_child_company("(AR) Hija de RI - propia (Unit Tests)", self.company_ri.vat)

        # Configuramos primero el candidato de la propia compañía del hijo (no tiene con qué
        # matchear todavía, así que crea su propia secuencia) y recién después el del padre
        # con el mismo prefijo. La búsqueda solo mira hacia arriba en la jerarquía, nunca hacia
        # abajo, así que quedan en secuencias independientes — si no se ordenara así, el
        # candidato del hijo caería al fallback del padre y el test no probaría nada.
        child_outgoing = self._create_picking_type(child_company, "outgoing", "OUT-CHILD-A")
        self._configure_delivery_guide(child_outgoing, self.document_type_remito, "00099")

        parent_outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-PARENT")
        self._configure_delivery_guide(parent_outgoing, self.document_type_remito, "00099")

        self.assertNotEqual(
            child_outgoing.l10n_ar_sequence_id,
            parent_outgoing.l10n_ar_sequence_id,
            "Setup inválido: deberían quedar independientes para que el test tenga sentido.",
        )

        child_internal = self._create_picking_type(child_company, "internal", "INT-CHILD")
        self._configure_delivery_guide(child_internal, self.document_type_remito, "00099")

        self.assertEqual(
            child_internal.l10n_ar_sequence_id,
            child_outgoing.l10n_ar_sequence_id,
            "Debe priorizar el match de la propia compañía por sobre el del padre.",
        )
        self.assertNotEqual(child_internal.l10n_ar_sequence_id, parent_outgoing.l10n_ar_sequence_id)

    def test_shared_sequence_falls_back_to_parent_company(self):
        """Sin match en la propia compañía, se busca en padre/hermanas con el mismo CUIT."""
        child_company = self._create_child_company("(AR) Hija de RI - fallback (Unit Tests)", self.company_ri.vat)

        parent_outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-PARENT2")
        self._configure_delivery_guide(parent_outgoing, self.document_type_remito, "00088")

        child_internal = self._create_picking_type(child_company, "internal", "INT-CHILD2")
        self._configure_delivery_guide(child_internal, self.document_type_remito, "00088")

        self.assertEqual(child_internal.l10n_ar_sequence_id, parent_outgoing.l10n_ar_sequence_id)

    def test_no_shared_sequence_between_siblings_with_different_vat(self):
        """El CAI es una autorización de ARCA atada a un CUIT: dos hijas del mismo padre con
        CUIT distinto son entidades fiscales distintas y no pueden compartir la secuencia,
        aunque coincidan el tipo de documento y el prefijo."""
        sibling_same_vat = self._create_child_company("(AR) Hija A - CUIT del padre (Unit Tests)", self.company_ri.vat)
        sibling_other_vat = self._create_child_company("(AR) Hija B - otro CUIT (Unit Tests)", "33693450239")

        outgoing_a = self._create_picking_type(sibling_same_vat, "outgoing", "OUT-SIB-A")
        self._configure_delivery_guide(outgoing_a, self.document_type_remito, "00066")

        internal_b = self._create_picking_type(sibling_other_vat, "internal", "INT-SIB-B")
        self._configure_delivery_guide(internal_b, self.document_type_remito, "00066")

        self.assertTrue(internal_b.l10n_ar_sequence_id, "Debería haberse creado una secuencia propia.")
        self.assertNotEqual(
            internal_b.l10n_ar_sequence_id,
            outgoing_a.l10n_ar_sequence_id,
            "Hermanas con CUIT distinto no deben compartir la secuencia del remito.",
        )

    def test_manual_sequence_assignment_is_respected(self):
        """Si el usuario ya asignó l10n_ar_sequence_id manualmente, el auto-match no la pisa."""
        outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-MANUAL")
        self._configure_delivery_guide(outgoing, self.document_type_remito, "00077")

        manual_sequence = self.env["ir.sequence"].create(
            {
                "name": "Manual sequence",
                "company_id": self.company_ri.id,
                "padding": 8,
                "implementation": "no_gap",
            }
        )
        internal = self._create_picking_type(self.company_ri, "internal", "INT-MANUAL")
        internal.l10n_ar_sequence_id = manual_sequence
        self._configure_delivery_guide(internal, self.document_type_remito, "00077")

        self.assertEqual(internal.l10n_ar_sequence_id, manual_sequence)

    def test_warning_when_editing_a_shared_sequence(self):
        """Clarificación 5: al tocar CAI/prefijo/rango de un picking type que ya comparte
        secuencia, se avisa (sin bloquear) qué otros tipos de operación se ven afectados."""
        outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-WARN")
        internal = self._create_picking_type(self.company_ri, "internal", "INT-WARN")
        self._configure_delivery_guide(outgoing, self.document_type_remito, "00050")
        self._configure_delivery_guide(internal, self.document_type_remito, "00050")
        self.assertEqual(internal.l10n_ar_sequence_id, outgoing.l10n_ar_sequence_id)

        result = outgoing._onchange_l10n_ar_warn_shared_sequence()

        self.assertIn("warning", result or {})
        self.assertIn(internal.display_name, result["warning"]["message"])

    def test_no_warning_when_sequence_is_not_shared(self):
        """Sin otros picking types compartiendo la secuencia, no hay warning."""
        outgoing = self._create_picking_type(self.company_ri, "outgoing", "OUT-NOWARN")
        self._configure_delivery_guide(outgoing, self.document_type_remito, "00051")

        result = outgoing._onchange_l10n_ar_warn_shared_sequence()

        self.assertIsNone(result)

    def test_no_warning_before_sequence_exists(self):
        """Sin l10n_ar_sequence_id todavía asignada (picking type nuevo), no hay warning."""
        internal = self._create_picking_type(self.company_ri, "internal", "INT-NEW")

        result = internal._onchange_l10n_ar_warn_shared_sequence()

        self.assertIsNone(result)
