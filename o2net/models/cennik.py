# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, AccessError, ValidationError

class VystavbaCennik(models.Model):
    _name = 'o2net.cennik'
    _description = "o2net - price list"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Code", size=30, help="Price list code")
    description = fields.Text(string="Description")  # popis
    platny_od = fields.Date(string="Valid from", required=True)
    platny_do = fields.Date(string="Valid to", required=True)
    dodavatel_id = fields.Many2one('res.partner', string='Vendor', required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)

    cennik_polozka_ids = fields.One2many('o2net.cennik.polozka', 'cennik_id', string='Items', copy=True)

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError(_('Price list with the same name already exists. Please choose an unique name.'))

class VystavbaCennikPolozka(models.Model):
    _name = 'o2net.cennik.polozka'
    _description = "o2net - price list item"

    cennik_id = fields.Many2one('o2net.cennik', string='Price list', required=True, ondelete='cascade')
    polozka_id = fields.Many2one('o2net.polozka', string='Item', required=True)
    name = fields.Char(related='polozka_id.name', string='Name')
    kod = fields.Char(related='polozka_id.kod', string='Code')
    is_balicek = fields.Boolean(related='polozka_id.is_balicek', string='Package')
    mj = fields.Selection(related='polozka_id.mj', string='Measure unit')
    popis = fields.Text(related='polozka_id.description', string='Description')
    cena = fields.Float(required=True, digits=(10, 2), string="Price")
    currency_id = fields.Many2one(related='cennik_id.currency_id', string='Currency')

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for po in self:
    #         result.append((po.id, po.name))
    #     return result
