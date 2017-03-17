# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Osoba(models.Model):
     _name = 'res.partner'
     _inherit = "res.partner"

     kod = fields.Char(string="Kód", size=10)
     cp_celkova_cena_limit = fields.Float(digits=(6,0), string="Celková cena cenovej ponuky", help="Cenový limit cenovej ponuky, pri ktorého prekročení musí CP schváli%t danaá osoba");
     reminder_interval = fields.Integer(string="Interval pripomienky", help="Po koľkých dňoch od poslednej pripomienky sa má opatovne poslať notifikácia (email)", default=0);