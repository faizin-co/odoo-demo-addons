from odoo import api, fields, models,_
from odoo.osv import expression
import json
from lxml import etree


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve')
    ], string='Status', readonly=True, index=True, copy=False, tracking=True, default='draft')

    def button_draft(self):
        self.write({'state': 'draft'})
        
    def button_approve(self):
        self.write({'state': 'approve'})

    @api.model
    def get_view(self, view_id=None, view_type=False, **options):
        result = super(ProductTemplate, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(result['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                node.set('readonly', 'state == "approve"')
        result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

class Product(models.Model):
    _inherit = "product.product"
    
    state = fields.Selection(related="product_tmpl_id.state")

    def button_draft(self):
        self.write({'state': 'draft'})
        
    def button_approve(self):
        self.write({'state': 'approve'})

