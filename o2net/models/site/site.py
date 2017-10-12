# -*- coding: utf-8 -*-

import base64
import datetime
import logging

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class Site(models.Model):
    _name = 'o2net.site'
    _description = "o2net - Site"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    HEADQUARTERS = 'headquarters'
    BRANCHOFFICE = 'branch office'
    POP = 'pop'

    SiteType = (
        (HEADQUARTERS, 'Headquarters'),
        (BRANCHOFFICE, 'Branch office'),
        (POP, 'POP')
    )

    name = fields.Char(string='Name')
    site_id = fields.Char(string='Site Id')
    customer = fields.Many2one('res.partner', string='Customer', ondelete='no action', required=True)
    site_type = fields.Selection(SiteType, string='Site Type', default=HEADQUARTERS)
    street = fields.Char(string='Street')
    register_no = fields.Char(string='Register No.')
    street_no = fields.Char(string='Street No.')
    city = fields.Char(string='City')
    zipcode = fields.Char(string='ZIP Code')
    country = fields.Many2one('res.country', string='Country', ondelete='no action')
    lon = fields.Char(string='Longtitude')
    lat = fields.Char(string='Latitude')
    altitude = fields.Char(string='Altitude')
    antena_height = fields.Char(string='The antenna height above the terrain')
    site_administration_person = fields.Char(string='Site administration person')
    site_administration_phone = fields.Char(string='Site administration phone')
    site_administration_email = fields.Char(string='Site administration email')
    site_operations_person = fields.Char(string='Site operations person')
    site_operations_phone = fields.Char(string='Site operations phone')
    site_operations_email = fields.Char(string='Site operations email')
    contract_term_end_date = fields.Date(string='Contract term end date')
    comment = fields.Text(string='Internal comment')
    # scomponents = fields.One2many('csr.service_component','site_id')
    #circuit_a = fields.One2many('o2.circuit', 'site_a')
    #circuit_b = fields.One2many('o2.circuit', 'site_b')
    cost_center = fields.Boolean(string='Cost Center')
    _sql_constraints = [('site_id_unique', 'unique(site_id)', 'site_id already exists!')]

    def create(self, cr, uid, vals, context=None):
        if not vals:
            vals = {}
        if context is None:
            context = {}
        vals['site_id'] = self.pool.get('ir.sequence').get(cr, uid, 'o2net.site.sequence')
        return super(Site, self).create(cr, uid, vals, context=context)
