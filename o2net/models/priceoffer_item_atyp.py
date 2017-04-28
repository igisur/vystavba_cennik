# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaCenovaPonukaPolozkaAtyp(models.Model):
    _name = 'o2net.cenova_ponuka.polozka_atyp'
    _description = "o2net - price offer atypical"

    name = fields.Char(required=True, string="Name", size=100, help="Code item")
    oddiel_id = fields.Many2one('o2net.oddiel', required=True, string="Section")
    cena = fields.Float(required=True, digits=(10, 2), string='Price')
    cenova_ponuka_id = fields.Many2one('o2net.cenova_ponuka', string='Price offer', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='cenova_ponuka_id.currency_id', string="Currency")
