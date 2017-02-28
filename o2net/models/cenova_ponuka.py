# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.tools.float_utils import float_is_zero, float_compare
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp import http
import datetime
import logging
import base64
import xmlrpclib
import urlparse
from openerp.addons.base.res.res_users import res_groups, res_users

# https://www.odoo.com/forum/help-1/question/how-to-display-dialog-box-16506

_logger = logging.getLogger(__name__)

class VystavbaCenovaPonuka(models.Model):
    _name = 'o2net.cenova_ponuka'
    _description = "vystavba - cenova ponuka"
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

    GROUP_SUPPLIER = 'o2net.group_vystavba_supplier'
    GROUP_PC = 'o2net.group_vystavba_pc'
    GROUP_PM = 'o2net.group_vystavba_pm'
    GROUP_MANAGER = 'o2net.group_vystavba_manager'
    GROUP_ADMIN = 'o2net.group_vystavba_admin'

    @api.one
    def action_exportSAP(self):
        # zavolat ako default pre self.sap_export_file_binary ak je CP v stave 'approved'
        # field 'sap_export_file_binary' viditelny iba v stave 'approved'
        export_file_name = 'sap_export_' + self.cislo + '_' + str(datetime.date.today()) + '.txt'
        _logger.info('export file name: ' + export_file_name)
        self.sap_export_file_name = export_file_name
        self.sap_export_content = self._get_sap_export_content()
        self.sap_export_file_binary = base64.encodestring(self.sap_export_content)
        self.message_post(body='<ul class ="o_mail_thread_message_tracking"><li>' + 'Subor "' + export_file_name + '" pre SAP bol vygenerovany' + "</li></ul>", message_type='email')

    @api.multi
    def _get_sap_export_content(self):
        data = []
        data.append('[PSPID]'+chr(9)+self.cislo)
        data.append('[WEMPF]'+chr(9)+'???')
        if self.dodavatel_id.kod:
            data.append('[MSTRT]'+chr(9)+self.dodavatel_id.kod)
        data.append('[MSCDT]' + chr(9) + datetime.strptime(self.datum_koniec, '%Y-%m-%d %H:%M:%S.%f'))

        query = """select
        zdroj.druh, concat(zdroj.kod,
                           CHR(9),
                           'JV',
                           CHR(9),
                           zdroj.cislo,
                           CHR(9),
                           case
        when
        zdroj.druh = '1T'
        then
        concat(cp.cislo, '.', o.name)
        when
        zdroj.druh = '2A'
        then
        concat(cp.cislo, '.', o.name)
        else
        cp.cislo
        end,
        CHR(9),
        to_char(cp.datum_koniec, 'DD.MM.YYYY')) as vystup
        from
        (
            select
        '1T' as druh, max(p.kod) as kod, sum(cena_celkom) as cislo, p.oddiel_id as oddiel_id, max(
            cpp.cenova_ponuka_id) as cenova_ponuka_id
        from vystavba_cenova_ponuka_polozka cpp
        join
        vystavba_cennik_polozka
        cp
        on
        cpp.cennik_polozka_id = cp.id
        join
        vystavba_polozka
        p
        on
        cp.polozka_id = p.id
        where
        cenova_ponuka_id = %s
                           and p.is_balicek = false
        group
        by
        p.oddiel_id
        union
        select
        '3B', p.kod, cpp.mnozstvo, p.oddiel_id, cpp.cenova_ponuka_id
        from vystavba_cenova_ponuka_polozka cpp
        join
        vystavba_cennik_polozka
        cp
        on
        cpp.cennik_polozka_id = cp.id
        join
        vystavba_polozka
        p
        on
        cp.polozka_id = p.id
        where
        cenova_ponuka_id = %s
                           and p.is_balicek = true
        union
        select
        '2A', atyp.name, cena, oddiel_id, cenova_ponuka_id
        from vystavba_cenova_ponuka_polozka_atyp atyp
        where
        cenova_ponuka_id = %s
        ) zdroj
        join
        vystavba_oddiel
        o
        on
        zdroj.oddiel_id = o.id
        join
        vystavba_cenova_ponuka
        cp
        on
        zdroj.cenova_ponuka_id = cp.id
        order
        by
        zdroj.druh;"""

        self.env.cr.execute(query, (self.id, self.id, self.id))
        fetchrows = self.env.cr.dictfetchall()

        for row in fetchrows:
            data.append(row.get('vystup'))
        # rozparsujem pole do stringu a oddelim enterom
        ret = '\r\n'.join(data)
        return ret

    @api.model
    def _get_default_osoba_priradena(self):
        self.osoba_priradena_id = self.env.user

    # limit partners to specific group
    @api.model
    def _partners_in_group(self, group_name):
        _logger.info("_partners_in_group: " + str(group_name))
        group = self.env.ref(group_name)
        partner_ids = []
        for user in group.users:
            partner_ids.append(user.partner_id.id)
        _logger.info("_partners_in_group: " + str(len(partner_ids)))
        return partner_ids

    @api.model
    def partners_in_group_supplier(self):
        partner_ids = self._partners_in_group(self.GROUP_SUPPLIER)
        return [('id', 'in', partner_ids)]

    def partners_in_group_pc(self):
        partner_ids = self._partners_in_group(self.GROUP_PC)
        return [('id', 'in', partner_ids)]

    def partners_in_group_pm(self):
        partner_ids = self._partners_in_group(self.GROUP_PM)
        return [('id', 'in', partner_ids)]

    def partners_in_group_manager(self):
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        return [('id', 'in', partner_ids)]

    @api.depends('cp_polozka_ids.cena_celkom','cp_polozka_atyp_ids.cena')
    def _amount_all(self):
        _logger.info("_amount_all: " + str(len(self)))
        for cp in self:
            cp_celkova_cena = 0.0
            for line in cp.cp_polozka_ids:
                cp_celkova_cena += line.cena_celkom

            for lineAtyp in cp.cp_polozka_atyp_ids:
                cp_celkova_cena += lineAtyp.cena

            cp.update({
                'celkova_cena': cp_celkova_cena
            })
            cp.update({'celkova_cena': cp_celkova_cena})

    @api.depends('dodavatel_id')
    def _compute_approved_cp_ids(self):
        self.approved_cp_ids = self.env['o2net.cenova_ponuka'].search(
            [
                ('state', '=', 'approved'),
                ('dodavatel_id.id', '=', self.dodavatel_id.id)
            ]
        )

    @api.one
    @api.depends('dodavatel_id','osoba_priradena_id')
    def _compute_ro_datumoddo(self):
        _logger.info("_compute_ro_datumoddo: " + str(len(self)))
        if self.osoba_priradena_id.id:
            if self.osoba_priradena_id.id == self.dodavatel_id.id:
                self.ro_datumoddo = False
            else:
                self.ro_datumoddo = True
        return {}

    ro_datumoddo = fields.Boolean(string="Ro datum OD DO", compute="_compute_ro_datumoddo")

    name = fields.Char(required=True, string="Názov", size=50, copy=False)
    cislo = fields.Char(string="Číslo projektu (PSID)", required=True, copy=False);
    financny_kod = fields.Char(string="Finančný kód", size=10, required=True, copy=False)
    skratka = fields.Char(string="Skratka", required=True, copy=False)
    datum_zaciatok = fields.Date(string="Dátum zahájenia", default=datetime.date.today());
    datum_koniec = fields.Date(string="Dátum ukončenia");
    poznamka = fields.Text(string="Poznámka", copy=False, track_visibility='onchange')
    wf_dovod = fields.Text(string="Dôvod pre workflow", copy=False, help='Uvedte dôvod pre zmenu stavu workflow, najme pri akcii "Vratiť na opravu" a "Zrušiť"')
    celkova_cena = fields.Float(compute='_amount_all', string='Celková cena', store=True, digits=(10,2), track_visibility='onchange')

    dodavatel_id = fields.Many2one('res.partner', required=True, string='Dodávateľ', track_visibility='onchange', domain=partners_in_group_supplier)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc)
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm)
    manager_id = fields.Many2one('res.partner', string='Manager', copy=False, track_visibility='onchange', domain=partners_in_group_manager)
    osoba_priradena_id = fields.Many2one('res.partner', string='Priradený', copy=False, track_visibility='onchange', default= lambda self: self.env.user.partner_id.id)
    state = fields.Selection(State, string='Stav', readonly=True, default='draft', track_visibility='onchange')

    cennik_id = fields.Many2one('o2net.cennik', string='Cenník')
    currency_id = fields.Many2one(related='cennik_id.currency_id', string="Mena")

    cp_polozka_ids = fields.One2many('o2net.cenova_ponuka.polozka', 'cenova_ponuka_id', string='Polozky', copy=False, track_visibility='onchange')
    cp_polozka_atyp_ids = fields.One2many('o2net.cenova_ponuka.polozka_atyp', 'cenova_ponuka_id', string='Atyp polozky', copy=False, track_visibility='onchange')

    sap_export_content = fields.Text(string="Export pre SAP", default='ABCDEFGH')
    sap_export_file_name = fields.Char(string="Export file name")
    sap_export_file_binary = fields.Binary(string='Export file')

    approved_cp_ids = fields.One2many('o2net.cenova_ponuka', compute=_compute_approved_cp_ids, string='Schvalene CP')


    @api.one
    def write(self, vals):
        self.ensure_one()

        res = super(VystavbaCenovaPonuka, self).write(vals)

        state = vals.get('state')
        _logger.info("WRITE: " + str(state))
        _logger.info("COND = " + str(vals.get('state') == None))
        # ak zapisujeme stav prisli sme sem z WF akcie, a preto koncime. automaticka zmena stavu WF je len v pripade akcie SAVE kde sa 'state' nemeni!
        if vals.get('state') == None:
            return res

        _logger.info("WRITE: user " + str(self.env.user.id))
        _logger.info("WRITE: user partner" + str(self.env.user.partner_id.id))
        _logger.info("WRITE: dodavatel " + str(self.dodavatel_id.id))
        _logger.info("WRITE: priradeny" + str(self.osoba_priradena_id.id))
        _logger.info("WRITE: stav " + str(self.state))

        # ak je prihlaseny Dodavatel, je mu priradena CP a je v stave ASSIGNED tak pri save zmenime stav na IN_PROGRESS
        if self.dodavatel_id.id == self.env.user.partner_id.id:
            _logger.info("WRITE: je prihlaseny dodavatel")
            if self.dodavatel_id.id == self.osoba_priradena_id.id:
                _logger.info("WRITE: je mu priradena CP")
                if self.state == self.ASSIGNED:
                    _logger.info("WRITE: CP je v stave ASSIGNED")
                    self.signal_workflow('in_progress')

        return res

    @api.one
    @api.onchange('dodavatel_id')
    def _find_cennik(self):
        result = {}
        if not self.dodavatel_id:
            return result
        _logger.info("Looking supplier's valid pricelist " + str(self.dodavatel_id.name))
        cennik_ids = self.env['o2net.cennik'].search([('dodavatel_id', '=', self.dodavatel_id.id),
                                                         ('platny_od', '<=', datetime.date.today()),
                                                         ('platny_do', '>', datetime.date.today())], limit = 1)

        for rec in cennik_ids:
            _logger.info(rec.name)

        if cennik_ids:
            self.cennik_id = cennik_ids[0]
        else:
            self.cennik_id = ''

        result = {'cennik_id': self.cennik_id}
        self.write(result)
        return result

    @api.onchange('osoba_priradena_id')
    def _sent_notification(self):
        # sent notification to assigned person
        _logger.info("Page URL: " + http.request.httprequest.full_path)

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
    # najdi partnera v skupine 'Manager', ktoreho field 'cena_na_schvalenie' je vacsia ako celkova cena CP
    def _find_manager(self):
        _logger.info("Looking for manager to approve order of price " + str(self.celkova_cena))
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        manager_ids = self.env['res.partner'].search([('id', 'in', partner_ids),('cp_celkova_cena_limit', '<=', self.celkova_cena)], order = "cp_celkova_cena_limit desc", limit = 1)

        for man in manager_ids:
            _logger.info(man.name)

        return manager_ids[0]

    @api.one
    def wf_draft(self):    # should be create but is set in field definition
        self.ensure_one()
        self.write({'state': self.DRAFT})
        return True

    @api.one
    def wf_assign_check(self):
        if self.dodavatel_id is False:
            raise AccessError("Cenova ponuka nema priradeneho dodavatela.")

        return True

    @api.one
    def wf_assign(self):
        _logger.info("workflow action to ASSIGN")
        self.ensure_one()
        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Dôvod pre workflow: " + self.wf_dovod + "</li></ul>")

        self.write({'state': self.ASSIGNED, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': ''})
        return True

    @api.one
    def wf_in_progress(self):
        _logger.info("workflow action to IN_PROGRESS")
        self.ensure_one()
        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Dôvod pre workflow: " + self.wf_dovod + "</li></ul>")

        self.write({'state': self.IN_PROGRESS, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': ''})
        return True

    @api.one
    def wf_approve(self):
        self.ensure_one()
        _logger.info("workflow action to APPROVE")

        # do historie pridame 'wf_dovod'
        if self.wf_dovod:
            # add to tracking values
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Dôvod pre workflow: " + self.wf_dovod + "</li></ul>")

        if self.osoba_priradena_id.id == self.dodavatel_id.id:
            #  Dodavatel poslal na schvalenie PC
            _logger.info("Supplier sent to approve by PC")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pc_id.id, 'wf_dovod': ''})

        elif self.osoba_priradena_id.id == self.pc_id.id:
            #  PC poslal na schvalenie PM
            _logger.info("PC sent to approve by PM")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pm_id.id, 'wf_dovod': ''})

        elif self.osoba_priradena_id.id == self.pm_id.id:   
            #  PM poslal na schvalenie Managerovy
            _logger.info("PM sent to approve by Manager")
            manager_id = self._find_manager()
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': manager_id.id, 'manager_id': manager_id.id, 'wf_dovod': ''})

        elif self.osoba_priradena_id.id == self.manager_id.id:
            #  Manager schvalil -> CP je schvalena a koncime
            _logger.info("Manager approved")
            self.write({'state': self.APPROVED, 'osoba_priradena_id': '', 'wf_dovod': ''})

        return True

    @api.one
    def wf_not_complete(self):
        _logger.info("workflow action to NOT_COMPLETE")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Dôvod pre workflow: " + self.wf_dovod + "</li></ul>")

        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.osoba_priradena_id.id == self.pc_id.id :
            _logger.info("workflow action to IN_PROGRESS")
            self.write({'state': self.IN_PROGRESS, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': ''})
            self.signal_workflow('not_complete')
            # call WF: signal "not complete". som v stave "to_approve". potrebujem ist do in_progers

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.osoba_priradena_id.id == self.pm_id.id :
            _logger.info("workflow action to TO_APPROVE")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pc_id.id, 'wf_dovod': ''})

        return True

    @api.one
    def wf_cancel(self):
        _logger.info("workflow action to CANCEL")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Dôvod pre workflow: " + self.wf_dovod + "</li></ul>")

        self.write({'state': self.CANCEL, 'osoba_priradena_id': '', 'wf_dovod': ''})
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

    @api.multi
    def send_mail(self):
        user_id = self.user_target.id
        body = self.message_target

        mail_details = {'subject': "Message subject",
                        'body': body
                        #'partner_ids': [(user_target)]
                        }

        mail = self.env['mail.thread']
        mail.message_post(type="notification", subtype="mt_comment", **mail_details)


class VystavbaCenovaPonukaPolozka(models.Model):
    _name = 'o2net.cenova_ponuka.polozka'
    _description = "vystavba - polozka cenovej ponuky"

    @api.depends('cena_jednotkova', 'mnozstvo')
    def _compute_cena_celkom(self):
        _logger.info("_compute_cena_celkom: " + str(len(self)))
        for line in self:
            if line.mnozstvo:
                line.cena_celkom = line.cena_jednotkova * line.mnozstvo

    @api.depends('cennik_polozka_id')
    def _compute_cena_jednotkova(self):
        _logger.info("_compute_cena_jednotkova: " + str(len(self)))
        for line in self:
            line.cena_jednotkova = line.cennik_polozka_id.cena

    cena_jednotkova = fields.Float(compute=_compute_cena_jednotkova, string='Jednotková cena', store=True, digits=(10, 2))
    cena_celkom = fields.Float(compute=_compute_cena_celkom, string='Cena celkom', store=True, digits=(10,2))
    mnozstvo = fields.Float(string='Množstvo', digits=(5,2), required=True)
    cenova_ponuka_id = fields.Many2one('o2net.cenova_ponuka', string='odkaz na cenovu ponuku', required=True, ondelete='cascade')
    cennik_polozka_id = fields.Many2one('o2net.cennik.polozka', string='Položka cenníka', required=True, domain="[('cennik_id', '=', parent.cennik_id)]")
    polozka_mj = fields.Selection(related='cennik_polozka_id.mj', string='Merná jednotka', stored=False)
    polozka_popis = fields.Text(related='cennik_polozka_id.popis', string='Popis', stored=False)
    name = fields.Char(related='cennik_polozka_id.name', string='Názov')
    kod = fields.Char(related='cennik_polozka_id.kod', string='Kód')

    currency_id = fields.Many2one(related='cenova_ponuka_id.currency_id', string="Mena")

class VystavbaCenovaPonukaPolozkaAtyp(models.Model):
    _name = 'o2net.cenova_ponuka.polozka_atyp'
    _description = "vystavba - atyp polozka cenovej ponuky"

    name = fields.Char(required=True, string="Nazov", size=30, help="Kod polozky")
    oddiel_id = fields.Many2one('o2net.oddiel', required=True, string="Oddiel")
    cena = fields.Float(required=True, digits=(10, 2))
    cenova_ponuka_id = fields.Many2one('o2net.cenova_ponuka', string='Cenová ponuka', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='cenova_ponuka_id.currency_id', string="Mena")
