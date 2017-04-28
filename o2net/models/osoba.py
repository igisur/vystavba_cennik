# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Osoba(models.Model):
     _name = 'res.partner'
     _inherit = "res.partner"

     kod = fields.Char(string="Code", size=10)
     cp_celkova_cena_limit = fields.Float(digits=(6,0), string="Price limit", help="In case the price limit is exceeded, price offer must be approved by a given person", default=0)
     reminder_interval = fields.Integer(string="Notification interval", help="Number of days, after which the notification will be send (email)", default=0)
