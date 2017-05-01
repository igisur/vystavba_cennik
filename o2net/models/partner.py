# -*- coding: utf-8 -*-

from openerp import models, fields, api


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = "res.partner"

    code = fields.Char(string="Code", size=10)
    po_total_price_limit = fields.Float(digits=(6, 0), string="Price limit",
                                        help="In case the price limit is exceeded, Quotation must be approved by a given person",
                                        default=0)
    reminder_interval = fields.Integer(string="Notification interval",
                                       help="Number of days, after which the notification will be send (email)",
                                       default=0)
