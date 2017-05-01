# -*- coding: utf-8 -*-

from openerp import models, fields, api

class o2netQuotationItemPackage(models.Model):
    _name = 'o2net.quotation.item_package'
    _inherit = 'o2net.quotation.item'
    _description = "o2net - Quotation package"
