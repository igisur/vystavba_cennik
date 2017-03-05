# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp import http
import datetime
import logging
import base64

#ivan.dian@o2.sk
#tomas.hellebrandt@o2.sk

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
        self.message_post(body='<ul class ="o_mail_thread_message_tracking"><li>' + 'Subor "' + export_file_name + '" pre SAP bol vygenerovany' + "</li></ul>")

    @api.multi
    def _get_sap_export_content(self):
        data = []
        if self.cislo:
            data.append('[PSPID]'+chr(9)+self.cislo)
        if self.pc_id.kod:
            data.append('[WEMPF]'+chr(9)+self.pc_id.kod)
        else:
            data.append('[WEMPF]' + chr(9) + '???')
        if self.dodavatel_id.kod:
            data.append('[MSTRT]'+chr(9)+self.dodavatel_id.kod)
        if self.datum_koniec:
            dt_obj = datetime.datetime.strptime(self.datum_koniec, DEFAULT_SERVER_DATE_FORMAT)
            dt_str = datetime.date.strftime(dt_obj, '%d.%m.%Y')
            _logger.info("datum koniec: " + dt_str)
            data.append('[MSCDT]' + chr(9) + dt_str)
        else:
            data.append('[MSCDT]' + chr(9) + '???')

        query = """ select
                        zdroj.druh, concat(zdroj.kod,
                        CHR(9),
                        'JV',
                        CHR(9),
                        zdroj.cislo,
                        CHR(9),
                        case
                            when zdroj.druh = '1T' then
                                concat(cp.cislo, '.', o.name)
                            when zdroj.druh = '2A' then
                                concat(cp.cislo, '.', o.name)
                        else
                            cp.cislo
                        end,
                        CHR(9),
                        to_char(cp.datum_koniec, 'DD.MM.YYYY')) as vystup
                    from
                        (   select
                                '1T' as druh, max(p.kod) as kod,
                                sum(cena_celkom) as cislo,
                                p.oddiel_id as oddiel_id,
                                max(cpp.cenova_ponuka_id) as cenova_ponuka_id
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id
                            where
                               cenova_ponuka_id = %s
                               and p.is_balicek = false
                            group by p.oddiel_id
                            union
                            select
                                '3B',
                                p.kod,
                                cpp.mnozstvo,
                                p.oddiel_id,
                                cpp.cenova_ponuka_id
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id
                            where
                                cenova_ponuka_id = %s
                                and p.is_balicek = true
                            union
                            select
                                '2A',
                                atyp.name,
                                cena,
                                oddiel_id,
                                cenova_ponuka_id
                            from o2net_cenova_ponuka_polozka_atyp atyp
                            where cenova_ponuka_id = %s
                        ) zdroj
                    join
                        o2net_oddiel o on zdroj.oddiel_id = o.id
                    join
                        o2net_cenova_ponuka cp on zdroj.cenova_ponuka_id = cp.id
                    order by zdroj.druh;"""

        self.env.cr.execute(query, (self.id, self.id, self.id))
        fetchrows = self.env.cr.dictfetchall()

        for row in fetchrows:
            data.append(row.get('vystup').decode('utf8'))
        # rozparsujem pole do stringu a oddelim enterom
        ret = '\r\n'.join(data)
        return ret

    @api.model
    def _get_default_osoba_priradena(self):
        self.osoba_priradena_id = self.env.user.partner_id

    # limit partners to specific group
    @api.model
    def _partners_in_group(self, group_name):
        group = self.env.ref(group_name)
        partner_ids = []
        for user in group.users:
            partner_ids.append(user.partner_id.id)
        _logger.info(str(len(partner_ids)) + " partners in group '" + str(group_name) + "'")
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

            cp.update({'celkova_cena': cp_celkova_cena})

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

    @api.one
    def _resolve_record_url(self):
        _logger.info("_resolve_record_url")
        base = self.env['ir.config_parameter'].get_param('web.base.url')
        id = self.id

        ir_model_data = self.env['ir.model.data']
        menu_id = ir_model_data.get_object_reference('o2net', 'menu_cenova_ponuka_preview')[1]
        action_id = ir_model_data.get_object_reference('o2net', 'action_window_cp_preview')[1]

        url = "%s/web#id=%s&view_type=form&model=o2net.cenova_ponuka&menu_id=%s&action=%s" % (base, id, menu_id, action_id)

        _logger.info("URL full path: " + http.request.httprequest.full_path)
        _logger.info("URL: " + url)

        self.base_url = url
        return {}

    @api.one
    def _get_rows(self, cp_id):
        data = []
        _logger.info("a_function_name")

        if cp_id:
            idecko = id
        else:
            idecko = 99

        _logger.info("a_function_name " + str(len(idecko)))

        query = """ select typ, cp.id as id, oddiel, polozka, cena_jednotkova, mj, pocet, cena_celkom, cp.cislo as cislo
                            from
                            (
                            select '1t' as typ, cpp.cenova_ponuka_id as cp_id, o.name as oddiel, p.name as polozka, cpp.cena_jednotkova as cena_jednotkova, p.mj as mj, cpp.mnozstvo as pocet, cpp.cena_celkom as cena_celkom
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = false
                            join o2net_oddiel o on p.oddiel_id = o.id
                            where cpp.cenova_ponuka_id = %s
                            union all
                            select '2a',cppa.cenova_ponuka_id, o.name, cppa.name, null, null, null, cppa.cena
                            from o2net_cenova_ponuka_polozka_atyp cppa
                            join o2net_oddiel o on cppa.oddiel_id = o.id
                            where cppa.cenova_ponuka_id = %s
                            union all
                            select '3b',cpp.cenova_ponuka_id, o.name, p.name, cpp.cena_jednotkova, p.mj, cpp.mnozstvo, cpp.cena_celkom
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = true
                            join o2net_oddiel o on p.oddiel_id = o.id
                            where cpp.cenova_ponuka_id = %s
                            ) zdroj
                            join o2net_cenova_ponuka cp on zdroj.cp_id = cp.id;"""

        # self.env.cr.execute(query, (self.id, self.id, self.id))
        self.env.cr.execute(query, (idecko, idecko, idecko))
        fetchrows = self.env.cr.dictfetchall()

        for row in fetchrows:
            data.append(row.get('vystup').decode('utf8'))

        return data

    ro_datumoddo = fields.Boolean(string="Ro datum OD DO", compute="_compute_ro_datumoddo")

    name = fields.Char(required=True, string="Názov", size=50, copy=True)
    cislo = fields.Char(string="Číslo projektu (PSID)", required=True, copy=True);
    financny_kod = fields.Char(string="Finančný kód", size=10, required=True, copy=True)
    skratka = fields.Char(string="Skratka", required=True, copy=True)
    datum_zaciatok = fields.Date(string="Dátum zahájenia", default=datetime.date.today(), copy=False);
    datum_koniec = fields.Date(string="Dátum ukončenia", copy=False);
    poznamka = fields.Text(string="Poznámka", track_visibility='onchange', copy=False)
    wf_dovod = fields.Text(string="Dôvod pre workflow", copy=False, help='Uvedte dôvod pre zmenu stavu workflow, najme pri akcii "Vratiť na opravu" a "Zrušiť"')
    celkova_cena = fields.Float(compute=_amount_all, string='Celková cena', store=True, digits=(10,2), track_visibility='onchange', copy=False)

    dodavatel_id = fields.Many2one('res.partner', required=True, string='Dodávateľ', track_visibility='onchange', domain=partners_in_group_supplier, copy=True)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc, copy=True)
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm, copy=True)
    manager_id = fields.Many2one('res.partner', string='Manager', track_visibility='onchange', domain=partners_in_group_manager, copy=False)
    osoba_priradena_id = fields.Many2one('res.partner', string='Priradený', copy=False, track_visibility='onchange', default= lambda self: self.env.user.partner_id.id)
    state = fields.Selection(State, string='Stav', readonly=True, default='draft', track_visibility='onchange', copy=False)

    cennik_id = fields.Many2one('o2net.cennik', string='Cenník', copy=True)
    currency_id = fields.Many2one(related='cennik_id.currency_id', string="Mena", copy=True)

    cp_polozka_ids = fields.One2many('o2net.cenova_ponuka.polozka', 'cenova_ponuka_id', string='Položky', track_visibility='onchange', copy=True)
    cp_polozka_atyp_ids = fields.One2many('o2net.cenova_ponuka.polozka_atyp', 'cenova_ponuka_id', string='Atyp položky', track_visibility='onchange', copy=True)

    #cp_polozky_rows = fields.Selection(selection=a_function_name, string='daky text')
    #cp_polozky_rows = fields.Selection(selection=a_function_name, string='daky text', default='draft', track_visibility='onchange')

    sap_export_content = fields.Text(string="Export pre SAP", default='ABCDEFGH', copy=False)
    sap_export_file_name = fields.Char(string="Export file name", copy=False)
    sap_export_file_binary = fields.Binary(string='Export file', copy=False)

    base_url = fields.Char(compute=_resolve_record_url, string="Link", store=False, copy=False, )

    @api.one
    def write(self, vals):
        self.ensure_one()

        # log changes in purchase order lines
        if 'cp_polozka_ids' in vals:
            record_history_tmpl = "<li><b>%s</b> %s</li>"
            msg = ""
            for record in vals.get('cp_polozka_ids'):
                _logger.info("record " + str(record))
                action_id = record[0]
                if action_id == 0:
                    id = record[2].get('cennik_polozka_id')
                    name = self.env['o2net.cennik.polozka'].browse(id).name
                    msg += record_history_tmpl % ('+++', name)
                elif action_id == 2:
                    id = record[1]
                    name = self.env['o2net.cenova_ponuka.polozka'].browse(id).name
                    msg += record_history_tmpl % ('---', name)

            self.message_post(body="<ul class =""o_mail_thread_message_tracking"">%s</ul>" % msg, message_type="notification")

        res = super(VystavbaCenovaPonuka, self).write(vals)

        state = vals.get('state')
        _logger.info("WRITE: " + str(state))
        # ak zapisujeme stav prisli sme sem z WF akcie, a preto koncime. automaticka zmena stavu WF je len v pripade akcie SAVE kde sa 'state' nemeni!
        if not vals.get('state') == None:
            return res

        _logger.info("WRITE: user " + str(self.env.user.id))
        _logger.info("WRITE: user partner " + str(self.env.user.partner_id.id))
        _logger.info("WRITE: dodavatel " + str(self.dodavatel_id.id))
        _logger.info("WRITE: priradeny " + str(self.osoba_priradena_id.id))
        _logger.info("WRITE: stav " + str(self.state))

        # ak je prihlaseny Dodavatel, je mu priradena CP a je v stave ASSIGNED tak pri save zmenime stav na IN_PROGRESS
        if self.dodavatel_id.id == self.env.user.partner_id.id:
            _logger.info("WRITE: je prihlaseny dodavatel")
            if self.dodavatel_id.id == self.osoba_priradena_id.id:
                _logger.info("WRITE: je mu priradena CP")
                if self.state == self.ASSIGNED:
                    _logger.info("WRITE: CP je v stave ASSIGNED")
                    _logger.info("WRITE: stav sa automaticky meni na IN_PROGRESS")
                    self.signal_workflow('in_progress')

        return res

    @api.multi
    def copy(self, default=None):

        # meno CP musi byt unikatne, preto pridame prefix. na koniec je lepsie, pretoze pri focuse ma input kurzor na konci -> uzivatel rychlo zmaze
        default = {'name': self.name + " [KOPIA]"}
        # ! treba zistit ci cennik_id je platny a prejst prilinokvane polozky a updatnut cenu !!!
        _logger.info("copy (duplicate): " + str(default))
        new_cp = super(VystavbaCenovaPonuka, self).copy(default=default)

        return new_cp

    @api.multi
    def unlink(self):
        # cenova ponuka moze byt zmazane len v stave "DRAFT". potom je mozne ju zrusit cez WF akciu "Cancel"
        if not self.state == self.DRAFT:
            raise AccessError("Cenovú ponuku je možné zmazať len pokiaľ je v stave 'Návrh'. V ostatnom prípade použite workflow akciu 'Zrušiť'")


    @api.one
    @api.onchange('dodavatel_id')
    def _find_cennik(self):
        result = {}
        if not self.dodavatel_id:
            return result

        _logger.info("Looking for supplier's valid pricelist " + str(self.dodavatel_id.name))
        cennik_ids = self.env['o2net.cennik'].search([('dodavatel_id', '=', self.dodavatel_id.id),
                                                         ('platny_od', '<=', datetime.date.today()),
                                                         ('platny_do', '>', datetime.date.today())], limit = 1)

        for rec in cennik_ids:
            _logger.info(rec.name)

        if cennik_ids:
            self.cennik_id = cennik_ids[0]
        else:
            self.cennik_id = ''

        # pri zmene dodavatela a tym padol aj cennika zmaz vsetky polozky
        self.cp_polozka_ids = None;

        result = {'cennik_id': self.cennik_id}
        self.write(result)
        return result

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
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        self.write({'state': self.ASSIGNED, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': ''})
        # send email to supplier
        self.send_mail([self.dodavatel_id.email])
        return True

    @api.one
    def wf_in_progress(self):
        _logger.info("workflow action to IN_PROGRESS")
        self.ensure_one()
        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        self.write({'state': self.IN_PROGRESS, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': ''})
        # notify PC via email that supplier starts wirking on CP
        # self.send_mail([self.dodavatel_id.email])
        return True

    @api.one
    def wf_approve(self):
        self.ensure_one()
        _logger.info("workflow action to APPROVE")

        # do historie pridame 'wf_dovod'
        if self.wf_dovod:
            # add to tracking values
            self.message_post(body='<ul class="o_mail_thread_message_tracking"><li>Workflow reason: ' + self.wf_dovod + '</li></ul>')

        if self.osoba_priradena_id.id == self.dodavatel_id.id:
            #  Dodavatel poslal na schvalenie PC
            _logger.info("Supplier sent to approve by PC")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pc_id.id, 'wf_dovod': ''})
            self.send_mail([self.pc_id.email])

        elif self.osoba_priradena_id.id == self.pc_id.id:
            #  PC poslal na schvalenie PM
            _logger.info("PC sent to approve by PM")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pm_id.id, 'wf_dovod': ''})
            self.send_mail([self.pm_id.email])

        elif self.osoba_priradena_id.id == self.pm_id.id:   
            #  PM poslal na schvalenie Managerovy
            _logger.info("PM sent to approve by Manager")
            manager_id = self._find_manager()
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': manager_id.id, 'manager_id': manager_id.id, 'wf_dovod': ''})
            self.send_mail([manager_id.email])

        elif self.osoba_priradena_id.id == self.manager_id.id:
            #  Manager schvalil -> CP je schvalena a koncime
            _logger.info("Manager approved")
            self.write({'state': self.APPROVED, 'osoba_priradena_id': '', 'wf_dovod': ''})
            self.send_mail([self.dodavatel_id.email, self.pc_id.email], template_name='mail_cp_approved')
            self.action_exportSAP()

        return True

    @api.one
    def wf_not_complete(self):
        _logger.info("workflow action to NOT_COMPLETE")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.osoba_priradena_id.id == self.pc_id.id :
            _logger.info("workflow action to IN_PROGRESS")
            self.write({'state': self.IN_PROGRESS, 'osoba_priradena_id': self.dodavatel_id.id, 'wf_dovod': ''})
            self.send_mail([self.dodavatel_id.email])
            self.signal_workflow('not_complete')
            # call WF: signal "not complete". som v stave "to_approve". potrebujem ist do in_progers

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.osoba_priradena_id.id == self.pm_id.id :
            _logger.info("workflow action to TO_APPROVE")
            self.write({'state': self.TO_APPROVE, 'osoba_priradena_id': self.pc_id.id, 'wf_dovod': ''})
            self.send_mail([self.pc_id.email])

        return True

    @api.one
    def wf_cancel(self):
        _logger.info("workflow action to CANCEL")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        self.write({'state': self.CANCEL, 'osoba_priradena_id': '', 'wf_dovod': ''})
        self.send_mail([self.dodavatel_id.email, self.pc_id.email], template_name='mail_cp_canceled')
        return True

    @api.one
    def action_sendMail(self):
        self.ensure_one()
        self.send_mail()
        return

    @api.one
    def send_mail(self, mail_to=None, template_name='mail_cp_assigned'):

        _logger.info("send mail to " + str(mail_to))

        # Find the e-mail template
        # definovane vo views/email_template.xml
        template = self.env.ref('o2net.' + template_name)
        if not template:
            _logger.info("unable send mail. template not found. template_name: " + str(template_name))
            return

        templateObj = self.env['mail.template'].browse(template.id)
        templateObj.email_from = 'odoo-mailer-daemon@o2network.sk'
        if mail_to:
            templateObj.email_to = ",".join(mail_to)
        mail_id = templateObj.send_mail(self.id, force_send=False, raise_exception=False)
        _logger.info("Mail sent: " + str(mail_id))


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
    cenova_ponuka_id = fields.Many2one('o2net.cenova_ponuka', string='Cenová ponuka', required=True, ondelete='cascade')
    cennik_polozka_id = fields.Many2one('o2net.cennik.polozka', string='Položka cenníka', required=True, domain="[('cennik_id', '=', parent.cennik_id)]")
    polozka_mj = fields.Selection(related='cennik_polozka_id.mj', string='Merná jednotka', stored=False)
    polozka_popis = fields.Text(related='cennik_polozka_id.popis', string='Popis', stored=False)
    name = fields.Char(related='cennik_polozka_id.name', string='Názov')
    kod = fields.Char(related='cennik_polozka_id.kod', string='Kód')

    currency_id = fields.Many2one(related='cenova_ponuka_id.currency_id', string="Mena")

class VystavbaCenovaPonukaPolozkaAtyp(models.Model):
    _name = 'o2net.cenova_ponuka.polozka_atyp'
    _description = "vystavba - atyp polozka cenovej ponuky"

    name = fields.Char(required=True, string="Nazov", size=100, help="Kod polozky")
    oddiel_id = fields.Many2one('o2net.oddiel', required=True, string="Oddiel")
    cena = fields.Float(required=True, digits=(10, 2))
    cenova_ponuka_id = fields.Many2one('o2net.cenova_ponuka', string='Cenová ponuka', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='cenova_ponuka_id.currency_id', string="Mena")
