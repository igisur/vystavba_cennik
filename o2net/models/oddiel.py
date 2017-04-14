# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaOddiel(models.Model):
    _name = 'o2net.oddiel'
    _description = "vystavba - oddiel"

    name = fields.Char(required=True, string="Code", size=30, help="Kód")
    description = fields.Text(string="Description")
    atypsluzba = fields.Char(string="KSZ", size=30)

