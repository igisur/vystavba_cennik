# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, AccessError, ValidationError

class VystavbaCennik(models.Model):
    _name = 'o2net.cennik'
    _description = "vystavba - cennik"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Kód", size=30, help="Kód cenníka")
    description = fields.Text(string="Popis")  # popis
    platny_od = fields.Date(string="Platný od", required=True)
    platny_do = fields.Date(string="Platný do", required=True)
    dodavatel_id = fields.Many2one('res.partner', string='Dodávateľ', required=True)
    currency_id = fields.Many2one('res.currency', string="Mena", required=True)

    cennik_polozka_ids = fields.One2many('o2net.cennik.polozka', 'cennik_id', string='Polozky', copy=True)

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Cenník s rovnakým názvom už existuje. Prosím zvoľte iný názov, ktorý bude unikátny.")

class VystavbaCennikPolozka(models.Model):
    _name = 'o2net.cennik.polozka'
    _description = "vystavba - polozka cennika"

    cennik_id = fields.Many2one('o2net.cennik', string='Cenník', required=True, ondelete='cascade')
    polozka_id = fields.Many2one('o2net.polozka', string='Položka', required=True)
    name = fields.Char(related='polozka_id.name', string='Názov')
    kod = fields.Char(related='polozka_id.kod', string='Kód')
    is_balicek = fields.Boolean(related='polozka_id.is_balicek', string='Balíček')
    mj = fields.Selection(related='polozka_id.mj', string='Merná jednotka')
    popis = fields.Text(related='polozka_id.description', string='Popis')
    cena = fields.Float(required=True, digits=(10, 2))
    currency_id = fields.Many2one(related='cennik_id.currency_id', string='Mena')

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for po in self:
    #         result.append((po.id, po.name))
    #     return result
