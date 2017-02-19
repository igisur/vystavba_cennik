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

    GROUP_SUPPLIER = 'vystavba.group_vystavba_supplier'
    GROUP_PC = 'vystavba.group_vystavba_pc'
    GROUP_PM = 'vystavba.group_vystavba_pm'
    GROUP_MANAGER = 'vystavba.group_vystavba_manager'

    @api.one
    def action_exportSAP(self):
        # zavolat ako default pre self.sap_export_file_binary ak je CP v stave 'approved'
        # field 'sap_export_file_binary' viditelny iba v stave 'approved'
        export_file_name = 'sap_export_' + self.cislo + '_' + str(datetime.date.today()) + '.txt'
        _logger.info('export file name: ' + export_file_name)
        self.sap_export_file_name = export_file_name
        self.sap_export_content = self._get_sap_export_content()
        self.sap_export_file_binary = base64.encodestring(self.sap_export_content)
        #self.sap_export_file_binary = base64.encodestring(self._get_sap_export_content())
        self.message_post(body='Subor "' + export_file_name + '" pre SAP bol vygenerovany', message_type='email')

    @api.multi
    def _get_sap_export_content(self):
        data = []
        data.append('[PSPID]'+chr(9)+self.cislo)
        data.append('[WEMPF]'+chr(9)+'???')
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
        group = self.env.ref(group_name)
        partner_ids = []
        for user in group.users:
            partner_ids.append(user.partner_id.id)
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

    @api.depends('celkova_cena')
    def _compute_celkova_cena_mena(self):
        _logger.info("_compute_celkova_cena_mena: " + str(len(self)))
        for line in self:
            celkova_cena_mena = ''
            #if line.cennik_polozka_id.cena:
            #    cena_za_mj = str(line.cennik_polozka_id.cena)
            #    if not line.polozka_mj == '_':
            #        cena_za_mj = cena_za_mj + '/' + str(line.polozka_mj)

            celkova_cena_text = 'Celková cena: '
            #line.celkova_cena_mena = celkova_cena_text.encode("utf-8") + str(line.celkova_cena) + ' ' + line.currency_id.symbol
            line.celkova_cena_mena =  (line.celkova_cena)+ ' ' + line.currency_id.symbol

    name = fields.Char(required=True, string="Názov", size=50, copy=False)
    cislo = fields.Char(string="Číslo projektu (PSID)", required=True, copy=False);
    financny_kod = fields.Char(string="Finančný kód", required=True, copy=False)
    skratka = fields.Char(string="Skratka", required=True, copy=False)
    datum_zaciatok = fields.Date(string="Dátum zahájenia", default=datetime.date.today());
    datum_koniec = fields.Date(string="Dátum ukončenia");
    poznamka = fields.Text(string="Poznámka", copy=False, track_visibility='onchange')
    wf_dovod = fields.Text(string="Dôvod pre workflow", copy=False, help='Uvedte dôvod pre zmenu stavu workflow, najme pri akcii "Vratiť na opravu" a "Zrušiť"')
    celkova_cena = fields.Float(compute='_amount_all', string='Celková cena', store=True, digits=(10,2), track_visibility='onchange')

    dodavatel_id = fields.Many2one('res.partner', required=True, string='Dodávateľ', track_visibility='onchange', domain=partners_in_group_supplier)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc)
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm)
    manager_id = fields.Many2one('res.partner', string='Manager', copy=False, track_visibility='onchange',  domain=partners_in_group_manager)
    osoba_priradena_id = fields.Many2one('res.partner', string='Priradený', copy=False, track_visibility='onchange', default= lambda self: self.env.user.partner_id.id)
    state = fields.Selection(State, string='Stav', readonly=True, default='draft', track_visibility='onchange')

    cennik_id = fields.Many2one('vystavba.cennik', string='Cenník')
    currency_id = fields.Many2one('res.currency', string="Mena")

    cp_polozka_ids = fields.One2many('vystavba.cenova_ponuka.polozka', 'cenova_ponuka_id', string='Polozky', copy=True, track_visibility='onchange')
    cp_polozka_atyp_ids = fields.One2many('vystavba.cenova_ponuka.polozka_atyp', 'cenova_ponuka_id', string='Atyp polozky', copy=False, track_visibility='onchange')

    sap_export_content = fields.Text(string="Export pre SAP", default='ABCDEFGH')
    sap_export_file_name = fields.Char(string="Export file name")
    sap_export_file_binary = fields.Binary(string='Export file')

    approved_cp_ids = fields.One2many('vystavba.cenova_ponuka', compute='_compute_approved_cp_ids', string='Schvalene CP')

    celkova_cena_mena = fields.Text(compute=_compute_celkova_cena_mena, string='Celková cena', store=True)

    @api.one
    @api.onchange('dodavatel_id')
    def _find_cennik(self):
        result = {}
        if not self.dodavatel_id:
            return result

        _logger.info("Looking supplier's valid pricelist " + str(self.dodavatel_id.name));
        cennik_ids = self.env['vystavba.cennik'].search([('dodavatel_id', '=', self.dodavatel_id.id),
                                                         ('platny_od', '<=', datetime.date.today()),
                                                         ('platny_do', '>', datetime.date.today())], limit = 1)
                                                         #('currency_id', '=', self.currency_id)],

        for rec in cennik_ids:
            _logger.info(rec.name);

        if cennik_ids:
            self.cennik_id = cennik_ids[0];
            self.currency_id = self.cennik_id.cennik_currency_id
            # musime zapisat rucne, pretoze fields oznacene na view ako READONLY sa nezapisuju :(
        else:
            self.cennik_id = '';
            self.currency_id = ''

        result = {'cennik_id': self.cennik_id, 'currency_id': self.currency_id}
        self.write(result);
        return result


    @api.depends('dodavatel_id')
    def _compute_approved_cp_ids(self):
        self.approved_cp_ids = self.env['vystavba.cenova_ponuka'].search(
            [
                ('state', '=', 'approved'),
                ('dodavatel_id.id', '=', self.dodavatel_id.id)
            ]
        )

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
        _logger.info("Looking for manager to approve order of price " + str(self.celkova_cena));
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        manager_ids = self.env['res.partner'].search([('id', 'in', partner_ids),('cp_celkova_cena_limit', '<=', self.celkova_cena)], order = "cp_celkova_cena_limit desc", limit = 1)

        for man in manager_ids:
            _logger.info(man.name);

        return manager_ids[0];

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
        if self.wf_dovod:
            self.message_post(body=self.wf_dovod)
            self.wf_dovod = ''

        self.write({'state': self.ASSIGNED, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': self.wf_dovod})
        return True

    @api.one
    def wf_in_progress(self):
        _logger.info("workflow action to IN_PROGRESS")
        self.ensure_one()
        if self.wf_dovod:
            self.message_post(body=self.wf_dovod)
            self.wf_dovod = ''

        self.write({'state': self.IN_PROGRESS, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': self.wf_dovod})
        return True

    @api.one
    def wf_approve(self):
        self.ensure_one()
        _logger.info("workflow action to APPROVE")
        self.write({})

        if self.wf_dovod:
            self.message_post(body=self.wf_dovod)
            self.wf_dovod = ''

        if self.osoba_priradena_id.id == self.dodavatel_id.id:
            #  Dodavatel poslal na schvalenie PC
            _logger.info("Supplier sent to approve by PC")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pc_id.id, 'wf_dovod': self.wf_dovod})

        elif self.osoba_priradena_id.id == self.pc_id.id:
            #  PC poslal na schvalenie PM
            _logger.info("PC sent to approve by PM")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pm_id.id, 'wf_dovod': self.wf_dovod})

        elif self.osoba_priradena_id.id == self.pm_id.id:
            #  PM poslal na schvalenie Managerovy
            _logger.info("PM sent to approve by Manager")
            manager_id = self._find_manager()
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': manager_id.id, 'manager_id': manager_id.id, 'wf_dovod': self.wf_dovod})

        elif self.osoba_priradena_id.id == self.manager_id.id:
            #  Manager schvalil -> CP je schvalena a koncime
            _logger.info("Manager approved")
            self.write({'state': self.APPROVED, 'osoba_priradena_id': '', 'wf_dovod': self.wf_dovod})

        return True

    @api.one
    def wf_not_complete(self):
        _logger.info("workflow action to NOT_COMPLETE")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body=self.wf_dovod)
            self.wf_dovod = ''

        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.osoba_priradena_id.id == self.pc_id.id :
            _logger.info("workflow action to IN_PROGRESS")
            self.write({'state': self.IN_PROGRESS, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': self.wf_dovod})
            self.signal_workflow('not_complete')
            # call WF: signal "not complete". som v stave "to_approve". potrebujem ist do in_progers

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.osoba_priradena_id.id == self.pm_id.id :
            _logger.info("workflow action to TO_APPROVE")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pc_id.id, 'wf_dovod': self.wf_dovod})

        return True

    @api.one
    def wf_cancel(self):
        _logger.info("workflow action to CANCEL")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body=self.wf_dovod)
            self.wf_dovod = ''

        self.write({'state': self.CANCEL, 'osoba_priradena_id': '', 'wf_dovod': self.wf_dovod})
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
    _name = 'vystavba.cenova_ponuka.polozka'
    _description = "Vystavba - polozka cenovej ponuky"

    @api.depends('cennik_polozka_id', 'polozka_mj')
    def _compute_cena_za_mj(self):
        for line in self:
            cena_za_mj = ''
            if line.cennik_polozka_id.cena:
                cena_za_mj = str(line.cennik_polozka_id.cena)
                if not line.polozka_mj == '_':
                    cena_za_mj = cena_za_mj + '/' + str(line.polozka_mj)

            line.cena_za_mj = cena_za_mj

    @api.depends('cena_jednotkova', 'mnozstvo')
    def _compute_cena_celkom(self):
        for line in self:
            total = line.cena_jednotkova * line.mnozstvo
            line.cena_celkom = total

    @api.depends('cennik_polozka_id')
    def _compute_cena_jednotkova(self):
        _logger.info("_compute_cena_jednotkova: " + str(len(self)))
        for line in self:
            line.cena_jednotkova = line.cennik_polozka_id.cena

    # cena = fields.Float(required=True, digits=(10, 2))
    cena_jednotkova = fields.Float(compute=_compute_cena_jednotkova, string='Jednotková cena', required=True, digits=(10,2))
    cena_celkom = fields.Float(compute=_compute_cena_celkom, string='Cena celkom', store=True, digits=(10,2))
    mnozstvo = fields.Float(string='Množstvo', digits=(5,2), required=True)
    cenova_ponuka_id = fields.Many2one('vystavba.cenova_ponuka', string='odkaz na cenovu ponuku', change_default=True, required=True, ondelete='cascade')
    cennik_polozka_id = fields.Many2one('vystavba.cennik.polozka', string='Položka cenníka',change_default=True, required=True, domain="[('cennik_id.dodavatel_id', '=', parent.dodavatel_id)]")
    polozka_mj = fields.Selection(related='cennik_polozka_id.polozka_mj', string='Merná jednotka')
    #mj = fields.Char(string='Merna jednotka', size=5, required=True, readonly=True)
    cena_za_mj = fields.Char(compute=_compute_cena_za_mj, string='Cena za mj', store=False)
    polozka_popis = fields.Text(related='cennik_polozka_id.polozka_popis', string='Položka popis')

    @api.onchange('cennik_polozka_id')
    def onchange_cennik_polozka_id(self):
        result = {}
        if not self.cennik_polozka_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        #self.date_planned = datetime.date.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if __name__ == '__main__':
            self.cena = self.cennik_polozka_id.get
        self.mj = 'ks'
        #self._suggest_quantity()
        #self._onchange_quantity()

        return result

class VystavbaCenovaPonukaPolozkaAtyp(models.Model):
    _name = 'vystavba.cenova_ponuka.polozka_atyp'
    _description = "Vystavba - polozka cenovej ponuky"

    name = fields.Char(required=True, string="Nazov", size=30, help="Kod polozky")
    oddiel_id = fields.Many2one('vystavba.oddiel', required=True, string="Oddiel")
    cena = fields.Float(required=True, digits=(10, 2))
    cenova_ponuka_id = fields.Many2one('vystavba.cenova_ponuka', string='odkaz na cenovu ponuku', required=True, ondelete='cascade')
