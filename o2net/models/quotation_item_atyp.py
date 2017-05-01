# -*- coding: utf-8 -*-

from openerp import models, fields, api

class o2netQuotationItemAtyp(models.Model):
    _name = 'o2net.quotation.item_atyp'
    _description = "o2net - Quotation atypical"

    name = fields.Char(required=True, string="Name", size=100, help="Code item")
    section_id = fields.Many2one('o2net.section', required=True, string="Section")
    price = fields.Float(required=True, digits=(10, 2), string='Price')
    quotation_id = fields.Many2one('o2net.quotation', string='Quotation', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='quotation_id.currency_id', string="Currency")
