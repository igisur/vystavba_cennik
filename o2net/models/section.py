# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaOddiel(models.Model):
    _name = 'o2net.oddiel'
    _description = "o2net - section"

    name = fields.Char(required=True, string="Code", size=30, help="Code")
    description = fields.Text(string="Description")
    atypservice = fields.Char(string="KSZ", size=30)

