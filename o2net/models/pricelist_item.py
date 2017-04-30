# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaCennikPolozka(models.Model):
    _name = 'o2net.cennik.polozka'
    _description = "o2net - price list item"

    price_list_id = fields.Many2one('o2net.cennik', string='Price list', required=True, ondelete='cascade')
    item_id = fields.Many2one('o2net.polozka', string='Item', required=True)
    price = fields.Float(required=True, digits=(10, 2), string="Price")

    name = fields.Char(related='item_id.name', string='Name')
    code = fields.Char(related='item_id.code', string='Code')
    is_package = fields.Boolean(related='item_id.is_package', string='Package')
    measure_unit = fields.Selection(related='item_id.measure_unit', string='Measure unit')
    description = fields.Text(related='item_id.description', string='Description')
    currency_id = fields.Many2one(related='price_list_id.currency_id', string='Currency')
