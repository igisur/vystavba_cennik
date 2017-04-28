# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaCennikPolozka(models.Model):
    _name = 'o2net.cennik.polozka'
    _description = "o2net - price list item"

    cennik_id = fields.Many2one('o2net.cennik', string='Price list', required=True, ondelete='cascade')
    polozka_id = fields.Many2one('o2net.polozka', string='Item', required=True)
    cena = fields.Float(required=True, digits=(10, 2), string="Price")

    name = fields.Char(related='polozka_id.name', string='Name')
    kod = fields.Char(related='polozka_id.kod', string='Code')
    is_balicek = fields.Boolean(related='polozka_id.is_balicek', string='Package')
    mj = fields.Selection(related='polozka_id.mj', string='Measure unit')
    popis = fields.Text(related='polozka_id.description', string='Description')
    currency_id = fields.Many2one(related='cennik_id.currency_id', string='Currency')
