# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, AccessError, ValidationError

class VystavbaCennik(models.Model):
    _name = 'o2net.cennik'
    _description = "o2net - price list"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Code", size=30, help="Price list code")
    description = fields.Text(string="Description")
    platny_od = fields.Date(string="Valid from", required=True)
    platny_do = fields.Date(string="Valid to", required=True)
    dodavatel_id = fields.Many2one('res.partner', string='Vendor', required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)

    cennik_polozka_ids = fields.One2many('o2net.cennik.polozka', 'cennik_id', string='Items', copy=True)

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError(_('Price list with the same name already exists. Please choose an unique name.'))
