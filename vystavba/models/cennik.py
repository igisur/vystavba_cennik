# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaCennik(models.Model):
    _name = 'vystavba.cennik'
    _description = "Vystavbovy cennik"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Kód", size=30, help="Kód cenníka")
    description = fields.Text(string="Popis")  # popis
    platny_od = fields.Date(string="Platný od", required=True)
    platny_do = fields.Date(string="Platný do", required=True)
    dodavatel_id = fields.Many2one('res.partner', string='Dodávateľ', required=True)
    cennik_currency_id = fields.Many2one('res.currency', string="Mena", required=True)

    cennik_polozka_ids = fields.One2many('vystavba.cennik.polozka', 'cennik_id', string='Polozky', copy=True)
    #polozka_id = fields.Many2one('vystavba.polozka', related='cennik_polozka_ids.polozka_id', string='Polozka')


class VystavbaCennikPolozka(models.Model):
    _name = 'vystavba.cennik.polozka'
    _description = "Vystavbovy cennik - cena polozky cennika pre konkretneho partnera"

    #name = fields.Char(related='polozka_id.name', string='Názov')
    kod = fields.Char(related='polozka_id.kod', string='Kód')
    popis = fields.Text(related='polozka_id.description', string='Popis')
    cena = fields.Float(required=True, digits=(10, 2))
    cennik_id = fields.Many2one('vystavba.cennik', string='Cenník', required=True, ondelete='cascade')
    polozka_id = fields.Many2one('vystavba.polozka', string='Položka', required=True)
    polozka_mj = fields.Selection(related='polozka_id.mj', string='Merná jednotka')
    polozka_popis = fields.Text(related='polozka_id.description', string='Popis')

    @api.multi
    def name_get(self):
        result = []
        for po in self:
            result.append((po.polozka_id.id, po.polozka_id.name))
        return result
