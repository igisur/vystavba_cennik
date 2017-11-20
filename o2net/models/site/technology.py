# -*- coding: utf-8 -*-

import base64
import datetime
import logging

from openerp import models, fields, api, SUPERUSER_ID
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class Technology(models.Model):
    _name = 'o2net.technology'
    _description = "o2net - technology"
    #_inherit = ['mail.thread', 'ir.needaction_mixin']

    GROUP_SUPPLIER = 'o2net.group_vendor'
    GROUP_PC = 'o2net.group_pc'
    GROUP_PM = 'o2net.group_pm'
    GROUP_MANAGER = 'o2net.group_manager'
    GROUP_ADMIN = 'o2net.group_admin'

    DRAFT = 'draft'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    AWAIT_TO_APPROVE = 'await_to_approve'
    APPROVED = 'approved'
    IMPLEMENTED = 'implemented'
    CANCEL = 'cancel'

    State = (
        (NEW, 'New'),
        (ASSIGNED, 'Assigned'),
        (IN_PROGRESS, 'In progress'),
        (AWAIT_TO_APPROVE, 'Await to approve'),
        (APPROVED, 'Approved'),
        (IMPLEMENTED, 'Implemented'),
    )


ntr - hotove dwg
akvizicia - najomna zmluva. notif na MW planner -> objedna u tusr frekvencie
pridelenie frekvencie TUSR - frekvencie, layout
realizacia - objedna sa tovar > koniec: tovar vydany/vyskladneny
vystavba - postavi mw, odovzda trans, dohodne integraciu
preberanie - zjednodusena papierovacka - doku: zakladna - revizie, meracie protokoly > prirani sa podla sablony -> dohonutie terminu prebierky (vendor, pc, ran prevadzkar, flm) > podpisanie zpk > odovzdanie dokumentacie Faza 2 akvizitorovy >  akvizitor potvrdi > koniec state:potvrdene
v prevadzke




prirad.osoba:  PM; priradi PC => state: assigned
prirad.osoba:  PC; priradi Vendora => state: in_progress
prirad.osoba:  vendor; zada datum draftu  => state: draft
prirad.osoba:  vendor; vypracuje predbeznu akviziciu a ntr (dwg, foto) => odoslat na odsuhlasenie state: schvalovanie -
prirad.osoba:  podla sablony sa priradia osoby mw planner, pc,  - 10dni v stave; planovac moze pripomienkovat (osoba, pripomienka, datum, stav (zamietnute, realizovat sa bude)) - pride notif dodavatelovy/pc  =>
 akcia "schvalene" - PC > state: schvalene

priradena osoba: vendor > zapracuje pripomienky > akcia:  state:   >

najomna zmluva - akvizicia

sablona:
 okres - planovac



    NET2G = '2g'
    NET3G = '3g'
    NET4G = '4g'
    NET35GHZ = '35ghz'
    NETTDD37GHZ = 'tdd37ghz'

    TechnologyType = (
        (NET2G, '2G'),
        (NET3G, '3G'),
        (NET4G, '4G'),
        (NETLTETDD, 'LTE TDD'),
        (NETMW, 'MW'),
    )

    JOB_NEW = "new_job"
    JOB_SALES = "sales_job"
    JOB_RECONFIG = "reconfig_job"

    JobType = (
        (JOB_NEW, 'new'),
        (JOB_SALES, 'sales'),
        (JOB_RECONFIG, 'reconfig')
    )

    # limit partners to specific group
    @api.model
    def _partners_in_group(self, group_name):
        group = self.sudo().env.ref(group_name)
        _logger.debug('Group: ' + group.name.encode('ascii', 'ignore'))
        partner_ids = []
        for user in group.users:
            _logger.debug('user: ' + user.name.encode('ascii', 'ignore'))
            partner_ids.append(user.partner_id.id)

        return partner_ids

    @api.model
    def partners_in_group_supplier(self):
        partner_ids = []

        if self.env.user.has_group(self.GROUP_SUPPLIER):
            if self.env.user.is_company:
                partner_ids.append(self.env.user.partner_id.id)
            else:
                partner_ids.append(self.env.user.partner_id.parent_id.id)
            return [('id', 'in', partner_ids)]

        group = self.sudo().env.ref(self.GROUP_SUPPLIER)
        for user in group.users:
            if user.partner_id.parent_id:
                vendor_id = user.partner_id.parent_id.id
                if not vendor_id in partner_ids:
                    partner_ids.append(vendor_id)
        return [('id', 'in', partner_ids)]

    @api.model
    def _get_default_vendor(self):
        _logger.debug('_get_default_vendor')
        ret = None

    type = fields.Selection(TechnologyType, string='Technology') # Technológia (2G / 3G / 4G / 4G / 3,5 GHz / TDD 3,7 GHz)
    active = fields.Boolean(string="Active", default=True, copy=False)
    state = fields.Selection(State, string='State', readonly=True, track_visibility='onchange', copy=False)


    site_id = fields.Many2one('o2net.site', string='Site', required=True, ondelete='cascade')
    job_type = fields.Selection(JobType, string='Job type', required=True) # Typ zadania (new / sales / reconfig)
    ! name = fields.Char(string='Name', required=True) # Názov
    vendor_id = fields.Many2one('res.partner', required=True, string='Vendor', track_visibility='onchange', domain=partners_in_group_supplier, copy=True)
    project_number = fields.Char(string="Project number (PSID)", required=True, copy=False)
    # psid_2g4g = fields.Char(string='PSID 2G/4G')  # PSID 2G/4G
    ! zo situ - financial_code = fields.Char(string="Financial code", size=10, required=True, copy=False)
    # fk = fields.Char(string='FK') # FK


    status = fields.Char(string='Status') # Status zadania
    address = fields.Char(string='Address') # Adresa/zadanie
    location_type = fields.Char(string='Location') # Typ lokality
    location_a_pole = fields.Char(string='A pole location') # Typ lokality A stoziar


    order_number = fields.Char(string='Order number') # p.č.

    nr_traffic_ranking = fields.Char(string='NR traffic ranking') # NR traffic ranking
    akv_inz_company_id = fields.Many2one('res.partner', string='AKV&INZ company', ondelete='no action') # Firma AKV&INZ
    install_company_id = fields.Many2one('res.partner', string='Install company', ondelete='no action') # Firma Inst.	PC
    akv = fields.Char(string='AKV') # AKV
    ran_planner = fields.Many2one('res.partner', string='RAN planner', ondelete='no action') # RAN planner
    mw_planner = fields.Many2one('res.partner', string='MW planner', ondelete='no action') # MW planner
    trans_spec = fields.Many2one('res.partner', string='TRANS spec', ondelete='no action') # TRANS spec
    job_sent_vendor_date = fields.Date(string='') # Zadanie odoslané dodávateľovi dňa
    pre_acq_report_sent_date= fields.Date(string='Report sent at') # Predakvizičná správa odovzdaná POC dňa
    site_survey_date = fields.Date(string='Site survey at') # Dátum site survey
    ntr_sent_date = fields.Date(string='NTR sent to vendor at') # Dátum zaslania NTR dodávateľom
    ntr_approved_date = fields.Date(string='NTR approved by O2 at') # Dátum schválenia NTR O2
    acq_report_sent_date = fields.Date(string='Acquisition report sent at') # Akvizičná správa odovzdaná POC dňa
    nz_close_date = fields.Date(string='NZ closed at') # NZ uzatvorená dňa (vrátane forecast)
    annual_rent = fields.Float(string='Annual rent', digits=(10, 2)) # Dohodnuté ročné nájomné
    doss_addressed_date = fields.Date(string='') # DOŠS oslovené dňa
    su_application_sent_date = fields.Date(string='') # Stavebný úrad – žiadosť podaná dňa
    su_permission_issued_date = fields.Date(string='') # Stavebný úrad – povolenie vydané dňa
    order_vendor_date = fields.Date(string='order_vendor_date') # Dátum zaslania CP dodávateľom PC
    order_akv_date = fields.Date(string='order_akv_date') # Dátum odoslania OBJ na AKV (Majka)
    order_inz_date = fields.Date(string='order_inz_date') # Dátum odoslania OBJ na INZ (Majka)
    order_install_date = fields.Date(string='order_install_date') # Dátum odoslania OBJ na inšt./integr. (Majka)
    bbu_eltek = fields.Char(string='BBU Eltek') # BBU Eltek (2200/1500/NIE)
    specification_date = fields.Date(string='Specification at') # Dátum špecifikácie HW
    date_3g = fields.Date(string='3G date ') # Dátum 3G OBJ Huawei (Majka)
    date_2g4g = fields.Date(string='2G/4G date') # Dátum 2G/4G OBJ Nokia (Majka)
    hw_in_stock = fields.Boolean(string='HW available in stock') # Dostupnosť HW na sklade (ANO / NIE)
    install_finish_date = fields.Date(string='Installation finished at') # Inštalácia dokončená dňa (vrátane forecast)
    mw_install_date = fields.Date(string='MW installation at') # Nová MW A+B strana nainštalovaná dňa (vrátane forecast)
    estimated_integration_date = fields.Date(string='Estimated integration date') # Predpokladaný termín integrácie (požiadavka dodavatela)
    integration_date = fields.Date(string='Integrated at (including NNS forecast)') # Zaintegrované dňa (vrátane NSS forecast)
    onair_date = fields.Date(string='On air') # Dátum ON Air
    flm_ran_acceptance_date = fields.Date(string='FKM+RAN acceptance') # Akceptácia FLM+RAN
    acceptance_issues_fixed_date = fields.Date(string='Acceptance issues fixed at') # Akceptačné nedostatky odstránené do
    stock_date = fields.Date(string='Stocked at') # Materiál preskladnený dňa
    acceptance_date = fields.Date(string='Acceptance at') # Fyzická akceptácia úspešne ukončená dňa
    full_reception = fields.Char(string='100% reception') # 100 % príjem (Majka)
    rfs_setup_date = fields.Date(string='RFS setup date') # Dátum nastavenia RFS (Slaninka)
    note = fields.Text(string='Note') # Poznamka
    _sql_constraints = [('site_type_unique', 'unique(site_id, type)', 'Such technology for site already exists!')]

    _defaults = {
        'type': 'NET2G',
        'state': 'DRAFT',
        'vendor_id': lambda self: self._get_default_vendor(),
    }

    @api.multi
    def write(self, vals):
        self.ensure_one()
        _logger.debug("technology write")
        _logger.debug("vals: " + str(vals))

        res = super(Technology, self).write(vals)

        # if STATE is written we came here from Workflow action and therefor we finish here. Automatic STATE change is only case of action 'SAVE'
        if not vals.get('state') == None:
            return res

        # change to 'IN_PROGRESS' if is in state 'ASSIGNED'
        if self.state == self.ASSIGNED:
            _logger.debug("autochange state from ASSIGNED to IN_PROGRESS")
            self.signal_workflow(self.IN_PROGRESS)

        return res

    @api.multi
    def wf_can_user_workflow(self):
        return True


