# -*- coding: utf-8 -*-

import time
import datetime

import openerp
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import api, fields, models, _
from openerp.exceptions import UserError


class o2netQuotationConfigSettings(models.TransientModel):
    _name = 'o2net.quotation.config.settings'
    _inherit = 'res.config.settings'

    sap_export_mail = fields.Char(size=128, string='Email for SAP export', help='Email to sent approved quotation and SAP export file')
