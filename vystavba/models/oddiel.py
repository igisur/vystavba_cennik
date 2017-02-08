# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaOddiel(models.Model):
    _name = 'vystavba.oddiel'
    _description = "Oddiel"

    # _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Kód", size=30, help="Kód")
    description = fields.Text(string="Popis")

    # osoba_id = fields.Many2One(comodel_name="vystavba.osoba", string="Osoba")
    # polozka_ids = fields.One2Many(comodel_name="vystavba.cennik.polozka", string="Polozky")
    # price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)

