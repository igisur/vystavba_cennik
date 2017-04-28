# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaPolozka(models.Model):
    _name = 'o2net.polozka'
    _description = "o2net - item"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Name", size=1000)
    kod = fields.Char(required=True, string="Code", size=30)
    description = fields.Text(string="Description", size=2000, default="")
    oddiel_id = fields.Many2one('o2net.oddiel', string='Section', required=False)
    mj = fields.Selection([
        ('_', 'Not given'),
        ('kg', 'Kilogram'),
        ('ks', 'Piece'),
        ('km', 'Kilometer'),
        ('hod', 'Hour'),
        ('m', 'Meter'),
        ('m2', 'Square meter'),
        ('m3', 'Cubic meter'),
        ('sada', 'Set'),
        ('bm', 'Standard meter'),
        ('vl.', 'VL'),
    ], string="Measure unit", default="_")
    is_balicek = fields.Boolean("Package", default=False)

    intern_id = fields.Char(string="Internal ID")
    intern_kod = fields.Char(string="Internal code")
