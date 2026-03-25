from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    so_id = fields.Many2one(
        "sale.order",
        string="Nomor SO",
        compute="_compute_so_id",
        store=True,
        readonly=False,  # biar tetap bisa diubah manual kalau perlu
        help="Terisi otomatis saat PO dibuat dari SO (dropship/MTO).",
    )

    @api.depends("order_line.sale_line_id.order_id")
    def _compute_so_id(self):
        for po in self:
            sales = po.order_line.mapped("sale_line_id.order_id")
            # kalau 1 PO berasal dari 1 SO -> isi otomatis
            po.so_id = sales.id if len(sales) == 1 else False
