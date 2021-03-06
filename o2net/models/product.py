# -*- coding: utf-8 -*-

from openerp import models, fields, api


class o2netProduct(models.Model):
    _name = 'o2net.product'
    _description = "o2net - item"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Name", size=1000)
    code = fields.Char(required=True, string="Code", size=30)
    description = fields.Text(string="Description", size=2000, default="")
    section_id = fields.Many2one('o2net.section', string='Section', required=False)
    unit_of_measure = fields.Selection([
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
        ('vl.', 'VL'),], string="Unit of measure", default="_")
    is_package = fields.Boolean("Package", default=False)

    intern_id = fields.Char(string="Internal ID")
    intern_code = fields.Char(string="Internal code")
