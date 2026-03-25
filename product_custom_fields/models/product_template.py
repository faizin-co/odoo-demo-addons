from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_catalog_number = fields.Char(
        string="Nomor Katalog",
        copy=False,
        index=True,
        help="Nomor katalog untuk identifikasi produk.",
    )
