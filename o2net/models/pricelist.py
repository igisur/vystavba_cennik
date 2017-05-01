# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, AccessError, ValidationError

class o2netPricelist(models.Model):
    _name = 'o2net.pricelist'
    _description = "o2net - price list"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Code", size=30, help="Price list code")
    description = fields.Text(string="Description")
    valid_from = fields.Date(string="Valid from", required=True)
    valid_to = fields.Date(string="Valid to", required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)

    pricelist_item_ids = fields.One2many('o2net.pricelist.item', 'price_list_id', string='Items', copy=True)

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError(_('Price list with the same name already exists. Please choose an unique name.'))
