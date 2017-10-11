# -*- coding: utf-8 -*-

import base64
import datetime
import logging

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class TechnicalProposal(models.Model):
    _name = 'o2net.tech.proposal'
    _description = "o2net - technical proposal"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Name')
    proposal_id = fields.Char(string='Proposal Id')
    site = fields.Many2one('o2net.site', string='Site', required=True)

    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')
