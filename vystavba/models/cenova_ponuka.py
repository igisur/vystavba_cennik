# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.tools.float_utils import float_is_zero, float_compare
from openerp.exceptions import UserError, AccessError, ValidationError
import datetime
import logging
import base64
import xmlrpclib
import urlparse
from openerp.addons.base.res.res_users import res_groups, res_users

# https://www.odoo.com/forum/help-1/question/how-to-display-dialog-box-16506

_logger = logging.getLogger(__name__)

class VystavbaCenovaPonuka(models.Model):
    _name = 'vystavba.cenova_ponuka'
    # _description = "Výstavbový cenník - cenová ponuka"
    _description = "Vystavbovy cennik - cenova ponuka"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    DRAFT = 'draft'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    TO_APPROVE = 'to_approve'
    APPROVED = 'approved'
    CANCEL = 'cancel'

    State = (
        (DRAFT, 'Návrh'),
        (ASSIGNED, 'Priradená'),
        (IN_PROGRESS, 'Rozpracovaná'),
        (TO_APPROVE, 'Na schválenie'),
        (APPROVED, 'Schválená'),
        (CANCEL, 'Zrušená')
    )

    @api.one
    def action_exportSAP(self):
        filecontent = "pokus"
        return xmlrpclib.response.make_response(filecontent, headers=[('Content-Type', 'application/txt')])

    # limit partners to specific group
    @api.model
    def _partners_in_group(self, group_name):
        group = self.env.ref(group_name)
        _logger.info("group name: " + group.name)
        partner_ids = []
        for user in group.users:
            _logger.info("user " + user.name + " /partner " + user.partner_id.name)
            partner_ids.append(user.partner_id.id)
        return partner_ids

    @api.model
    def partners_in_group_supplier(self):
        partner_ids = self._partners_in_group('vystavba.group_vystavba_supplier')
        return [('id', 'in', partner_ids)]

    def partners_in_group_pc(self):
        partner_ids = self._partners_in_group('vystavba.group_vystavba_pc')
        return [('id', 'in', partner_ids)]

    def partners_in_group_pm(self):
        partner_ids = self._partners_in_group('vystavba.group_vystavba_pm')
        return [('id', 'in', partner_ids)]

    def partners_in_group_manager(self):
        partner_ids = self._partners_in_group('vystavba.group_vystavba_manager')
        return [('id', 'in', partner_ids)]

    name = fields.Char(required=True, string="Názov", size=50, copy=False)
    cislo = fields.Char(string="Číslo projektu (PSID)", required=True, copy=False);
    financny_kod = fields.Char(string="Finančný kód", required=True, copy=False)
    skratka = fields.Char(string="Skratka", required=False, copy=False)
    datum_zaciatok = fields.Date(string="Dátum zahájenia", default=datetime.date.today());
    datum_koniec = fields.Date(string="Dátum ukončenia");
    poznamka = fields.Text(string="Poznámka", copy=False)
    celkova_cena = fields.Float(string='Celkova cena', digits=(10,2), copy=False)

    # related field to vystavba.cennik.dodavatel_id
    # cennik_id = fields.related(related='vystavba.cennik.id', store=True)

    dodavatel_id = fields.Many2one('res.partner', string='Dodávateľ', track_visibility='onchange', domain=partners_in_group_supplier)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc)
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm)
    manager_id = fields.Many2one('res.partner', string='Manager', copy=False, track_visibility='onchange',  domain=partners_in_group_manager)
    osoba_priradena_id = fields.Many2one('res.partner', string='Priradený', copy=False, track_visibility='onchange')
    state = fields.Selection(State, string='Stav', readonly=True, default='draft', track_visibility='onchange')

    cp_polozka_ids = fields.One2many('vystavba.cenova_ponuka.polozka', 'cenova_ponuka_id', string='Polozky', copy=True, track_visibility='onchange')
    cp_polozka_atyp_ids = fields.One2many('vystavba.cenova_ponuka.polozka_atyp', 'cenova_ponuka_id', string='Atyp polozky', copy=False, track_visibility='onchange')

    sap_file = base64.encodestring('ABCDEFGH')
    sap_export = fields.Binary(string='Export pre SAP', default=sap_file)

    approved_cp_ids = fields.One2many('vystavba.cenova_ponuka', compute='_compute_approved_cp_ids', string='Schvalene CP')

    @api.depends('dodavatel_id')
    def _compute_approved_cp_ids(self):
        self.approved_cp_ids = self.env['vystavba.cenova_ponuka'].search(
            [
                ('state', '=', 'approved'),
                ('dodavatel_id.id', '=', self.dodavatel_id.id)
            ]
        )

    @api.one
    def copy_polozky(self):
        _logger.info("Copy polozky")
        return []

    # @api.model
    # def create(self, args):
    #     self._standardize(args)
    #     return super(Model, self).create(args) -> global name 'Model' is not defined

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            #raise ValidationError("Cenova ponuka s nazvom "" %s "" uz existuje. Prosim zvolte iny nazov, ktory bude unikatny." % self.name)
            raise ValidationError("Cenová ponuka s rovnakým názvom už existuje. Prosím zvolte iný názov, ktorý bude unikátny.")

    # Workflow
    @api.one
    def wf_draft(self):    # should be create but is set in field definition
        self.ensure_one()
        self.write({'state': self.DRAFT})
        return True

    @api.one
    def wf_assign_check(self):
        return not self.dodavatel_id is False

    @api.one
    def wf_assign(self):
        _logger.info("workflow action to ASSIGN")
        self.ensure_one()
        self.write({'state': self.ASSIGNED, 'osoba_priradena_id': self.dodavatel_id.id})
        return True

    @api.one
    def wf_in_progress(self):
        _logger.info("workflow action to IN_PROGRESS")
        self.ensure_one()
        self.write({'state': self.IN_PROGRESS})
        return True

    # Dodavatel odoslal vyplnenu CP na schvalenie. skonci na PC
    @api.one
    def wf_to_approve(self):
        _logger.info("workflow action to TO_APPROVE")
        self.ensure_one()
        self.write({'state': self.TO_APPROVE})
        self.write({'osoba_priradena_id': self.pc_id.id})
        return True


    # najdi partnera v skupine 'Manager', ktoreho field 'cena_na_schvalenie' je vacsia ako celkova cena CP
    def find_manager(self):
        # !!!! self.env['res.users'].browse(self.env.uid).has_group('base.group_sale_manager') !!!
        manager_id = self.manager_id.id
        if self.celkova_cena > 3000:
            manager_id = self.uid;

        return manager_id;

    @api.one
    def wf_approve(self):
        self.ensure_one()
        _logger.info("workflow action to APPROVE")
        self.write({'state': self.TO_APPROVE})

        if self.osoba_priradena_id.id == self.dodavatel_id.id:
            #  Dodavatel poslal na schvalenie PC
            _logger.info("Supplier sent to approve by PC")
            self.write({'osoba_priradena_id': self.pc_id.id})

        elif self.osoba_priradena_id.id == self.pc_id.id:
            #  PC poslal na schvalenie PM
            _logger.info("PC sent to approve by PM")
            self.write({'osoba_priradena_id': self.pm_id.id})

        elif self.osoba_priradena_id.id == self.pm_id.id:
            #  PM poslal na schvalenie Managerovy
            _logger.info("PM sent to approve by PM")
            self.write({'osoba_priradena_id': self.manager_id.id})

        elif self.osoba_priradena_id.id == self.manager_id.id:
            #  Manager schvalil -> CP je schvalena a koncime
            _logger.info("PM sent to approve by Manager")
            self.write({'osoba_priradena_id': '', 'state': 'approved'})

        # self.signal_workflow('action_assign')
        return True

    @api.one
    def wf_not_complete(self):
        _logger.info("workflow action to NOT_COMPLETE")
        self.ensure_one()
        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.osoba_priradena_id.id == self.pc_id.id :
            _logger.info("workflow action to IN_PROGRESS")
            self.write({'osoba_priradena_id': self.dodavatel_id.id, 'state': self.IN_PROGRESS})
            self.signal_workflow('not_complete')
            # call WF: signal "not complete". som v stave "to_approve". potrebujem ist do in_progers

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.osoba_priradena_id.id == self.pm_id.id :
            _logger.info("workflow action to TO_APPROVE")
            self.write({'osoba_priradena_id': self.pc_id.id, 'state': self.TO_APPROVE})

        return True

    @api.one
    def wf_cancel(self):
        _logger.info("workflow action to CANCEL")
        self.ensure_one()
        self.write({'state': self.CANCEL})
        self.write({'osoba_priradena_id': ''})
        return True

    @api.multi
    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


class VystavbaCenovaPonukaPolozka(models.Model):
    _name = 'vystavba.cenova_ponuka.polozka'
    _description = "Vystavba - polozka cenovej ponuky"

    cena = fields.Float(required=True, digits=(10, 2))
    mnozstvo = fields.Float(string='Mnozstvo', digits=(5,2), required=True)
    cenova_ponuka_id = fields.Many2one('vystavba.cenova_ponuka', string='odkaz na cenovu ponuku', required=True, ondelete='cascade')

    cennik_polozka_id = fields.Many2one('vystavba.cennik.polozka', string='Polozka cennika', required=True)
    #polozka_id = fields.Reference('vystavba.polozka', string='Polozka', required=False)


class VystavbaCenovaPonukaPolozkaAtyp(models.Model):
    _name = 'vystavba.cenova_ponuka.polozka_atyp'
    _description = "Vystavba - polozka cenovej ponuky"

    name = fields.Char(required=True, string="Nazov", size=30, help="Kod polozky")
    oddiel_id = fields.Many2one('vystavba.oddiel', required=True, string="Oddiel")

    cena = fields.Float(required=True, digits=(10, 2))
    mnozstvo = fields.Float(string='Mnozstvo', digits=(5,2), required=True)

    cenova_ponuka_id = fields.Many2one('vystavba.cenova_ponuka', string='odkaz na cenovu ponuku', required=True, ondelete='cascade')
