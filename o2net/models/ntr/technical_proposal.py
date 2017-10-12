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

    NET2G = '2g'
    NET3G4G = '3g4g'
    NET4G = '4g'
    NET35GHZ = '35ghz'
    NETTDD37GHZ = 'tdd37ghz'

    TechnologyType = (
        (NET2G, '2G'),
        (NET3G4G, '3G / 4G'),
        (NET4G, '4G'),
        (NET35GHZ, '3,5 Ghz'),
        (NETTDD37GHZ, 'TDD 3,7 Ghz'),
    )

    JOB_NEW = "new_job"
    JOB_SALES = "sales_job"
    JOB_RECONFIG = "reconfig_job"

    JobType = (
        (JOB_NEW, 'new'),
        (JOB_SALES, 'sales'),
        (JOB_RECONFIG, 'reconfig'),
    )

    site_id = fields.Many2one('o2net.site', string='Site', required=False)
    order_number = fields.Char(string='Order number') # p.č.
    nr_traffic_ranking = fields.Char(string='NR traffic ranking') # NR traffic ranking
    status = fields.Char(string='Status') # Status zadania
    fk = fields.Char(string='FK') # FK
    psid_2g4g = fields.Char(string='PSID 2G/4G') # PSID 2G/4G
    name = fields.Char(string='Name') # Názov
    address = fields.Char(string='Address') # Adresa/zadanie
    location_type = fields.Char(string='Location') # Typ lokality
    job_type = fields.Selection(JobType, string='Job type') # Typ zadania (new / sales / reconfig)
    location_a_pole = fields.Char(string='A pole location') # Typ lokality A stoziar
    technology = fields.Selection(TechnologyType, string='Technology', default=NET2G) # Technológia (2G / 3G / 4G / 4G / 3,5 GHz / TDD 3,7 GHz)
    akv_inz_company_id = fields.Many2one('res.partner', string='AKV&INZ company', ondelete='no action') # Firma AKV&INZ
    install_company_id = fields.Many2one('res.partner', string='Install company', ondelete='no action') # Firma Inst.	PC
    akv = fields.Char(string='AKV') # AKV
    ran_planner = fields.Char(string='RAN planner') # RAN planner
    mw_planner = fields.Char(string='MW planner') # MW planner
    trans_spec = fields.Char(string='TRANS spec') # TRANS spec
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
