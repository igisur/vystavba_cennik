# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaOddiel(models.Model):
    _name = 'o2.vys.oddiel'
    _description = "vystavba - oddiel"

    name = fields.Char(required=True, string="Kód", size=30, help="Kód")
    description = fields.Text(string="Popis")

