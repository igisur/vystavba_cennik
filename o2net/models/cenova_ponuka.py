# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp import http
import datetime
import logging
import base64

_logger = logging.getLogger(__name__)

class VystavbaCenovaPonuka(models.Model):
    _name = 'o2net.cenova_ponuka'
    _description = "o2net - price offer"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    DRAFT = 'draft'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    TO_APPROVE = 'to_approve'
    APPROVED = 'approved'
    CANCEL = 'cancel'

    State = (
        (DRAFT, 'Draft'),
        (ASSIGNED, 'Assigned'),
        (IN_PROGRESS, 'In progress'),
        (TO_APPROVE, 'To approve'),
        (APPROVED, 'Approved'),
        (CANCEL, 'Cancel')
    )

    GROUP_SUPPLIER = 'o2net.group_vystavba_supplier'
    GROUP_PC = 'o2net.group_vystavba_pc'
    GROUP_PM = 'o2net.group_vystavba_pm'
    GROUP_MANAGER = 'o2net.group_vystavba_manager'
    GROUP_ADMIN = 'o2net.group_vystavba_admin'

    @api.model
    def do_check_approve(self):
        # validation of waiting for till Quotation is approved
        # called from cron
        _logger.debug('do_check_approve')
        today = datetime.datetime.now()
        schvalene = self.search([('state', '=', 'to_approve')])
        for row in schvalene:
            if not row.manager_ids:
                _logger.debug('manager nie je nasetovany !!!!')
                continue

            _logger.debug('manager = '+str(row.manager_ids))

            for manager in row.manager_ids:

                query = """select date(mm.date) as datum
                                    from mail_mail m
                                    join mail_mail_res_partner_rel mrespartner on m.id = mrespartner.mail_mail_id
                                    join res_partner p on mrespartner.res_partner_id = p.id
                                    join mail_message mm on m.mail_message_id = mm.id
                                    where mrespartner.res_partner_id = %s
                                    order by mm.date desc
                                    limit 1;"""

                self.env.cr.execute(query, ([manager.id]))
                fetchrow = self.env.cr.fetchone()
                rozdiel = abs((today - datetime.datetime.strptime(fetchrow[0], DEFAULT_SERVER_DATE_FORMAT)).days)
                _logger.debug('rozdiel ' + str(rozdiel) + ' ---- je na schvalenie pocet dni: ' + str(manager.reminder_interval))
                if rozdiel >  manager.reminder_interval:
                    #poslem mail
                    self.send_mail([manager], template_name='mail_manager_warning')

    def get_last_mail_date(self, partner_id):
        ret = {}

        # najdeme posledny mail odoslany partnerovy
        mail_ids = self.env['mail.mail'].search([('', '=', partner_id)], order = "cp_celkova_cena_limit desc", limit=1)

        return ret;

    @api.one
    def action_exportSAP(self):
        export_file_name = 'sap_export_' + self.cislo + '_' + str(datetime.date.today()) + '.txt'
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
            _logger.debug("datum koniec: " + dt_str)
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
                                '1T' as druh,
                         		max(p.intern_kod) as kod,
                                sum(cena_celkom) as cislo,
                                p.oddiel_id as oddiel_id,
                                max(cpp.cenova_ponuka_id) as cenova_ponuka_id
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id
                            where
                               cenova_ponuka_id = %s
                               and p.is_balicek = false
                            group by p.oddiel_id,p.intern_kod
                            union
                         	select
                         		'2A',
                         		(select atypsluzba from o2net_oddiel where id = atyp.oddiel_id),
                         		sum(cena),
                          		atyp.oddiel_id,
                                max(atyp.cenova_ponuka_id)
                            from o2net_cenova_ponuka_polozka_atyp atyp
                            where cenova_ponuka_id = %s
                            group by atyp.oddiel_id
                         	union
                            select
                                '3B',
                                p.kod,
                                cpp.mnozstvo,
                                p.oddiel_id,
                                cpp.cenova_ponuka_id
                            from o2net_cenova_ponuka_polozka_balicek cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id
                            where
                                cenova_ponuka_id = %s
                                and p.is_balicek = true

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

    @api.depends('cp_polozka_ids.cena_celkom','cp_polozka_balicek_ids.cena_celkom','cp_polozka_atyp_ids.cena')
    def _compute_amount_all(self):
        for cp in self:
            cp_celkova_cena = 0.0
            for line in cp.cp_polozka_ids:
                cp_celkova_cena += line.cena_celkom

            for line in cp.cp_polozka_balicek_ids:
                cp_celkova_cena += line.cena_celkom

            for lineAtyp in cp.cp_polozka_atyp_ids:
                cp_celkova_cena += lineAtyp.cena

            cp.update({'celkova_cena': cp_celkova_cena})

    @api.one
    @api.depends('dodavatel_id','osoba_priradena_ids')
    def _compute_ro_datumoddo(self):
        if self.osoba_priradena_ids:
            self.ro_datumoddo = not self.dodavatel_id.id in self.osoba_priradena_ids.ids

    def _compute_is_user_assigned(self):
        ret = self.env.user.partner_id.id in self.osoba_priradena_ids.ids
        self.is_user_assigned = ret
        return ret

    @api.depends('osoba_priradena_ids')
    def _compute_can_user_exec_wf(self):
        ret = self.is_user_assigned or self.env.user.id == SUPERUSER_ID
        return ret

    @api.one
    def _compute_record_url(self):
        base = self.env['ir.config_parameter'].get_param('web.base.url')
        id = self.id
        ir_model_data = self.env['ir.model.data']
        menu_id = ir_model_data.get_object_reference('o2net', 'menu_cenova_ponuka_preview')[1]
        action_id = ir_model_data.get_object_reference('o2net', 'action_window_cp_preview')[1]
        url = "%s/web#id=%s&view_type=form&model=o2net.cenova_ponuka&menu_id=%s&action=%s" % (base, id, menu_id, action_id)
        _logger.debug("URL: " + url)
        self.base_url = url

    @api.one
    def _get_oddiel(self, cp_id):
        data = []
        _logger.debug("_get_oddiel " + str(cp_id))

        query = """select zdroj.id as id, zdroj.oddiel as oddiel
                            from
                            (
                            select o.ID as id,o.name as oddiel
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = false
                            join o2net_oddiel o on p.oddiel_id = o.id
                            where cpp.cenova_ponuka_id = %s
                            union all
                            select o.ID, o.name
                            from o2net_cenova_ponuka_polozka_atyp cppa
                            join o2net_oddiel o on cppa.oddiel_id = o.id
                            where cppa.cenova_ponuka_id = %s
                            ) zdroj
                            group by zdroj.id, zdroj.oddiel
                            order by zdroj.oddiel;"""

        self.env.cr.execute(query, (cp_id,cp_id))
        data = self.env.cr.dictfetchall()
        _logger.debug("_get_oddiel data " + str(data))

        if data:
            return data
        else:
            return {}

    @api.one
    def _get_rows_oddiel_typ(self, cp_id, oddiel_id):
        data = []
        _logger.debug("_get_rows_oddiel_typ " + str(cp_id) + ", " + str(oddiel_id))

        query = """ select  cpp.cenova_ponuka_id as cp_id,
                            o.name as oddiel,
                            p.intern_kod as ksz,
                            p.name as polozka,
                            p.mj as mj,
                            cpp.mnozstvo as pocet,
                            cpp.cena_jednotkova as cena_jednotkova,
                            cpp.cena_celkom as cena_celkom
                    from o2net_cenova_ponuka_polozka cpp
                        join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                        join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = false
                        join o2net_oddiel o on p.oddiel_id = o.id
                    where cpp.cenova_ponuka_id = %s
                        and o.id = %s;"""

        self.env.cr.execute(query, (cp_id, oddiel_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_rows_oddiel_atyp(self, cp_id, oddiel_id):
        data = []
        _logger.debug("_get_rows_oddiel_atyp " + str(cp_id) + ", " + str(oddiel_id))

        query = """ select  cppa.cenova_ponuka_id as cp_id,
                            o.name as oddiel,
                            cppa.name as polozka,
                            cppa.cena as cena_celkom
                    from o2net_cenova_ponuka_polozka_atyp cppa
                    join o2net_oddiel o on cppa.oddiel_id = o.id
                    where cppa.cenova_ponuka_id = %s
                        and o.id = %s;"""

        self.env.cr.execute(query, (cp_id, oddiel_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_rows_oddiel_balicek(self, cp_id):
        data = []
        _logger.debug("_get_rows_oddiel_balicek " + str(cp_id))

        query = """select   cpp.cenova_ponuka_id as cp_id,
                            o.name as oddiel,
                            p.kod as kod,
                            p.name as polozka,
                            p.mj as mj,
                            cpp.cena_jednotkova,
                            cpp.mnozstvo as pocet,
                            cpp.cena_celkom as cena_celkom
                    from o2net_cenova_ponuka_polozka_balicek cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = true
                            join o2net_oddiel o on p.oddiel_id = o.id
                        where cpp.cenova_ponuka_id = %s   ;"""

        self.env.cr.execute(query, ([cp_id]))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_price_oddiel(self, cp_id, oddiel_id):
    # -------------------------------------------------------------
    # celkova cena pre cenovu ponuku a oddiel
    # pocitaju sa polozky typove a atypove spolu podla oddielu
    # -------------------------------------------------------------

        cena = 0
        _logger.debug("_get_price_oddiel cp_id=" + str(cp_id) + " oodiel_id=" + str(oddiel_id))

        query = """select sum(zdroj.cena)
                    from
                    (   select sum(cppa.cena) as cena
                        from o2net_cenova_ponuka cp
                        join o2net_cenova_ponuka_polozka_atyp cppa on cp.id = cppa.cenova_ponuka_id
                        join o2net_oddiel o on cppa.oddiel_id = o.id
                        where cp.id = %s
                        and o.id = %s
                        union all
                        select sum(cpp.cena_celkom)
                        from o2net_cenova_ponuka cp
                        join o2net_cenova_ponuka_polozka cpp on cp.id = cpp.cenova_ponuka_id
                        join o2net_cennik_polozka c on cpp.cennik_polozka_id = c.id
                        join o2net_polozka p on c.polozka_id = p.id
                        where cp.id = %s
                        and p.oddiel_id = %s
                        and p.is_balicek = false ) zdroj;"""

        self.env.cr.execute(query, (cp_id, oddiel_id, cp_id, oddiel_id))
        cena = self.env.cr.fetchone()[0]
        _logger.debug("_get_price_oddiel cena=" + str(cena))

        return cena

    @api.one
    def _get_price_oddiel_atyp(self, cp_id, oddiel_id, atyp):
    # --------------------------------------------------------------------------
    # celkova cena pre cenovu ponuku a oddiel a typ/atyp
    # pocita as suma pre cp a oddiel a polozky typove resp. atypove polozky
    # --------------------------------------------------------------------------
        cena = 0
        _logger.debug("_get_price_oddiel_atyp cp_id=" + str(cp_id) + " oodiel_id=" + str(oddiel_id)+ " atyp=" + str(atyp))

        if atyp==1:
            #1 atypove polozky
            query = """select sum(cppa.cena)
                        from o2net_cenova_ponuka cp
                        join o2net_cenova_ponuka_polozka_atyp cppa on cp.id = cppa.cenova_ponuka_id
                        join o2net_oddiel o on cppa.oddiel_id = o.id
                        where
                            cp.id = %s
                            and o.id = %s;"""

            self.env.cr.execute(query, (cp_id, oddiel_id))
            cena = self.env.cr.fetchone()[0]

        if atyp==0:
            query = """select sum(cpp.cena_celkom)
                        from o2net_cenova_ponuka cp
                        join o2net_cenova_ponuka_polozka cpp on cp.id = cpp.cenova_ponuka_id
                        join o2net_cennik_polozka c on cpp.cennik_polozka_id = c.id
                        join o2net_polozka p on c.polozka_id = p.id
                        where cp.id = %s
                        and p.oddiel_id = %s
                        and p.is_balicek = false;"""

            self.env.cr.execute(query, (cp_id, oddiel_id))
            cena = self.env.cr.fetchone()[0]

        _logger.debug("_get_price_oddiel_atyp cena=" + str(cena))
        return cena

    @api.one
    def _get_price_balicky(self, cp_id):
    # ---------------------------------------------
    # celkova cena pre cenovu ponuku a balicky
    # ---------------------------------------------
        cena = 0
        _logger.debug("_get_price_balicky cp_id=" + str(cp_id))

        query = """select sum(cpp.cena_celkom)
                    from o2net_cenova_ponuka cp
                    join o2net_cenova_ponuka_polozka_balicek cpp on cp.id = cpp.cenova_ponuka_id
                    join o2net_cennik_polozka c on cpp.cennik_polozka_id = c.id
                    join o2net_polozka p on c.polozka_id = p.id
                    where cp.id = %s
                    and p.is_balicek = true;"""

        self.env.cr.execute(query, ([cp_id]))
        cena = self.env.cr.fetchone()[0]
        return cena

    @api.one
    def _get_rows(self, cp_id):
        data = []
        _logger.debug("a_function_name " + str(cp_id))

        query = """ select  typorder as typorder,
                            typ as typ,
                            oddieltyp as oddieltyp,
                            cp.id as id,
                            oddiel as oddiel,
                            ksz as ksz,
                            polozka as polozka,
                            cena_jednotkova as cena_jednotkova,
                            mj as mj,
                            pocet as pocet,
                            cena_celkom as cena_celkom,
                            cp.cislo as cislo
                            from
                            (
                            select  '1t' as typorder,
                                    't' as typ,
                                    concat(o.name,'p') as oddieltyp,
                                    cpp.cenova_ponuka_id as cp_id,
                                    o.name as oddiel,
                                    p.intern_kod as ksz,
                                    p.name as polozka,
                                    cpp.cena_jednotkova as cena_jednotkova,
                                    p.mj as mj,
                                    cpp.mnozstvo as pocet,
                                    cpp.cena_celkom as cena_celkom
                            from o2net_cenova_ponuka_polozka cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = false
                            join o2net_oddiel o on p.oddiel_id = o.id
                            where cpp.cenova_ponuka_id = %s
                            union all
                            select  '2a',
                                    'a',
                                    concat(o.name,'p'),
                                    cppa.cenova_ponuka_id,
                                    o.name,
                                    '',
                                    cppa.name,
                                    null,
                                    null,
                                    null,
                                    cppa.cena
                            from o2net_cenova_ponuka_polozka_atyp cppa
                            join o2net_oddiel o on cppa.oddiel_id = o.id
                            where cppa.cenova_ponuka_id = %s
                            union all
                            select  '3b',
                                    'b',
                                    concat(o.name,'b'),
                                    cpp.cenova_ponuka_id,
                                    o.name,
                                    p.kod,
                                    p.name,
                                    cpp.cena_jednotkova,
                                    p.mj,
                                    cpp.mnozstvo,
                                    cpp.cena_celkom
                            from o2net_cenova_ponuka_polozka_balicek cpp
                            join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                            join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = true
                            join o2net_oddiel o on p.oddiel_id = o.id
                            where cpp.cenova_ponuka_id = %s
                            ) zdroj
                            join o2net_cenova_ponuka cp on zdroj.cp_id = cp.id order by typorder;"""

        # self.env.cr.execute(query, (self.id, self.id, self.id))
        self.env.cr.execute(query, (cp_id, cp_id, cp_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.model
    def _get_default_pc(self):
        _logger.debug('_get_default_pc')
        # PC - ak ativny user je PC, tak ho rovno predvolime
        partners = self._partners_in_group(self.GROUP_PC)
        _logger.debug('partners: ' + str(partners))

        ret = None
        if self.env.user.partner_id.id in partners:
            _logger.debug('current user is PC. will be used as default PC.')
            ret = self.env.user.partner_id.id

        return ret

    def _get_cp_polozka_ids(self):
        _logger.debug('_get_polozka_ids')
        for record in self:
            _logger.debug('record:' + str(record))
            record.cp_polozka_ids = self.env['o2net.cenova_ponuka.polozka'].search([('cenova_ponuka_id', '=', record.id), ('cennik_polozka_id.is_balicek', '!=', True)])

    def _get_cp_polozka_balicek_ids(self):
        _logger.debug('_get_polozka_balicek_ids')
        for record in self:
            _logger.debug('record:' + str(record))
            record.cp_polozka_balicek_ids = self.env['o2net.cenova_ponuka.polozka'].search([('cenova_ponuka_id', '=', record.id), ('cennik_polozka_id.is_balicek', '=', True)])

    def _set_polozka_ids(self):
        self.ensure_one()
        _logger.debug('_set_polozka_balicek_ids')
        _logger.debug('polozky: ' + str(self.polozka_ids))
        #self.write({'polozka_ids': [(6, 0, [self.dodavatel_id.id])]})

        for record in self.cp_polozka_ids:
            _logger.debug('polozka: ' + str(record))
            self.polozka_ids = record

        for record in self.cp_polozka_balicek_ids:
            _logger.debug('balicek: ' + str(record))
            self.polozka_ids = record

        _logger.debug('polozky: ' + str(self.polozka_ids))

    # FIELDS
    # computed fields
    ro_datumoddo = fields.Boolean(string="RO date From To", compute=_compute_ro_datumoddo, store=False, copy=False)
    can_user_exec_wf = fields.Boolean(string="Can user execute workflow action", compute=_compute_can_user_exec_wf, store=False, copy=False)
    is_user_assigned = fields.Boolean(string="Is current user assigned", compute=_compute_is_user_assigned)

    name = fields.Char(required=True, string="Name", size=50, copy=True)
    cislo = fields.Char(string="Project number (PSID)", required=True, copy=True);
    financny_kod = fields.Char(string="Financial code", size=10, required=True, copy=True)
    skratka = fields.Char(string="Short name", required=True, copy=True)
    datum_zaciatok = fields.Date(string="Start date", default=datetime.date.today(), copy=False);
    datum_koniec = fields.Date(string="End date", copy=False);
    poznamka = fields.Text(string="Note", track_visibility='onchange', copy=False)
    wf_dovod = fields.Text(string='Workflow reason', copy=False, help='Enter workflow reason mainly for actions "Return for repair" and "Cancel"')
    celkova_cena = fields.Float(compute=_compute_amount_all, string='Total price', store=True, digits=(10, 2), track_visibility='onchange', copy=False)
    dodavatel_id = fields.Many2one('res.partner', required=True, string='Vendor', track_visibility='onchange', domain=partners_in_group_supplier, copy=True)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc, copy=True, default=lambda self: self._get_default_pc())
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm, copy=True)
    manager_ids = fields.Many2many('res.partner', relation="o2net_cenova_ponuka_manager_rel", string='Manager', domain=partners_in_group_manager, copy=False)
    osoba_priradena_ids = fields.Many2many('res.partner', relation="o2net_cenova_ponuka_assigned_rel", string='Assigned persons', copy=False, default = lambda self: [(4,self.env.user.partner_id.id)])

    state = fields.Selection(State, string='State', readonly=True, default='draft', track_visibility='onchange', copy=False)
    state_date = fields.Date(string="date state", default=datetime.date.today(), copy=False);
    cennik_id = fields.Many2one('o2net.cennik', string='Price list', copy=True)
    currency_id = fields.Many2one(related='cennik_id.currency_id', string="Currency", copy=True)

    cp_polozka_ids = fields.One2many('o2net.cenova_ponuka.polozka', 'cenova_ponuka_id', string='Items', track_visibility='onchange', copy=True)
    cp_polozka_balicek_ids = fields.One2many('o2net.cenova_ponuka.polozka_balicek', 'cenova_ponuka_id', string='Packages', track_visibility='onchange', copy=True)
    cp_polozka_atyp_ids = fields.One2many('o2net.cenova_ponuka.polozka_atyp', 'cenova_ponuka_id', string='Atypical items', track_visibility='onchange', copy=True)

    sap_export_content = fields.Text(string="Export for SAP", default='ABCDEFGH', copy=False)
    sap_export_file_name = fields.Char(string="Export file name", copy=False)
    sap_export_file_binary = fields.Binary(string='Export file', copy=False)

    base_url = fields.Char(compute=_compute_record_url, string="Link", store=False, copy=False, )

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # log changes in Quotation's items
        if 'cp_polozka_ids' in vals:
            record_history_tmpl = "<li><b>%s</b> %s</li>"
            msg = ""
            for record in vals.get('cp_polozka_ids'):
                _logger.debug("record " + str(record))
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

        # ak zapisujeme stav prisli sme sem z WF akcie, a preto koncime. automaticka zmena stavu WF je len v pripade akcie SAVE kde sa 'state' nemeni!
        if not vals.get('state') == None:
            return res

        # ak je prihlaseny Dodavatel, je mu priradena CP a je v stave ASSIGNED tak pri save zmenime stav na IN_PROGRESS
        if self.dodavatel_id.id in self.osoba_priradena_ids.ids:
            _logger.debug("CP je priradena dodavatelovy")
            if self.state == self.ASSIGNED:
                _logger.debug("CP je v stave ASSIGNED > stav sa automaticky meni na IN_PROGRESS")
                self.signal_workflow('in_progress')

        return res

    @api.multi
    def copy(self, default=None):

        # meno CP musi byt unikatne, preto pridame prefix. na koniec je lepsie, pretoze pri focuse ma input kurzor na konci -> uzivatel rychlo zmaze
        default = {'name': self.name + " [KOPIA]"}
        # ! treba zistit ci cennik_id je platny a prejst prilinokvane polozky a updatnut cenu !!!
        _logger.debug("copy (duplicate): " + str(default))
        new_cp = super(VystavbaCenovaPonuka, self).copy(default=default)

        return new_cp

    @api.multi
    def unlink(self):
        # cenova ponuka moze byt zmazane len v stave "DRAFT". potom je mozne ju zrusit cez WF akciu "Cancel"
        if not self.state == self.DRAFT:
            raise AccessError("Cenovú ponuku je možné zmazať len pokiaľ je v stave 'Návrh'. V ostatnom prípade použite workflow akciu 'Zrušiť'")

    @api.onchange('dodavatel_id')
    def _find_cennik(self):
        result = {}
        if not self.dodavatel_id:
            return result

        _logger.debug("Looking for supplier's valid pricelist " + str(self.dodavatel_id.name))
        cennik_ids = self.env['o2net.cennik'].search([('dodavatel_id', '=', self.dodavatel_id.id),
                                                         ('platny_od', '<=', datetime.date.today()),
                                                         ('platny_do', '>', datetime.date.today())], limit = 1)

        for rec in cennik_ids:
            _logger.debug(rec.name)

        if cennik_ids:
            self.cennik_id = cennik_ids[0]
        else:
            self.cennik_id = ''

        # pri zmene dodavatela a tym padol aj cennika zmaz vsetky polozky
        self.cp_polozka_ids = None;

        result = {'cennik_id': self.cennik_id}
        self.write(result)
        return result

    @api.onchange('state')
    def _set_state_date(self):
        self.state_date = datetime.date.today()

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            #raise ValidationError("Cenova ponuka s nazvom "" %s "" uz existuje. Prosim zvolte iny nazov, ktory bude unikatny." % self.name)
            raise ValidationError("Cenová ponuka s rovnakým názvom už existuje. Prosím zvolte iný názov, ktorý bude unikátny.")

    # Workflow
    # najdi partnera v skupine 'Manager', ktoreho field 'cena_na_schvalenie' je vacsia ako celkova cena CP
    def _find_managers(self):
        _logger.debug("Looking for manager to approve order of price " + str(self.celkova_cena))
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        manager_ids = self.env['res.partner'].search([('id', 'in', partner_ids),('cp_celkova_cena_limit', '<=', self.celkova_cena)], order = "cp_celkova_cena_limit desc")

        _logger.debug("Found managers: " + str(manager_ids.ids))
        for man in manager_ids:
            _logger.debug(man.name)

        return manager_ids

    @api.multi
    def wf_draft(self):    # should be create but is set in field definition
        self.ensure_one()
        self.write({'state': self.DRAFT})
        return True

    @api.multi
    def wf_assign_check(self):
        self.ensure_one()
        if self.dodavatel_id is False:
            raise AccessError(_("Price offer does not have vendor assigned"))

        return True

    @api.multi
    def wf_can_user_workflow(self):
        self.ensure_one()

        ret = self._compute_can_user_exec_wf()

        if ret is False:
            raise AccessError(_("You do not have permission for workflow action"))

        return ret

    @api.one
    def wf_assign(self):
        _logger.debug("workflow action to ASSIGN")
        self.ensure_one()
        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        self.sudo().write({'state': self.ASSIGNED, 'osoba_priradena_ids': [(6,0,[self.dodavatel_id.id])], 'wf_dovod': ''})
        self.sudo().send_mail([self.dodavatel_id])
        return True

    @api.one
    def wf_in_progress(self):
        _logger.debug("workflow action to IN_PROGRESS")
        self.ensure_one()
        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        self.sudo().write({'state': self.IN_PROGRESS, 'osoba_priradena_ids': [(6,0,[self.dodavatel_id.id])], 'wf_dovod': ''})
        # notify PC via email that supplier starts working on CP
        self.sudo().send_mail([self.pc_id], template_name='mail_cp_in_progress')
        return True

    @api.one
    def wf_approve(self):
        self.ensure_one()
        _logger.debug("workflow action to APPROVE")

        # do historie pridame 'wf_dovod'
        if self.wf_dovod:
            # add to tracking values
            self.message_post(body='<ul class="o_mail_thread_message_tracking"><li>Workflow reason: ' + self.wf_dovod + '</li></ul>')

        # Dodavatel poslal na schvalenie PC
        if self.dodavatel_id.id in self.osoba_priradena_ids.ids:
            _logger.debug("Supplier sent to approve by PC")
            self.sudo().write({'state': self.TO_APPROVE, 'osoba_priradena_ids': [(6,0,[self.pc_id.id])], 'wf_dovod': ''})
            self.sudo().send_mail([self.pc_id])

        # PC poslal na schvalenie PM
        elif self.pc_id.id in self.osoba_priradena_ids.ids:
            _logger.debug("PC sent to approve by PM")
            self.sudo().write({'state': self.TO_APPROVE, 'osoba_priradena_ids': [(6,0,[self.pm_id.id])], 'wf_dovod': ''})
            self.sudo().send_mail([self.pm_id])

        # PM poslal na schvalenie Managerovy
        elif self.pm_id.id in self.osoba_priradena_ids.ids:
            _logger.debug("PM sent to approve by Manager")
            manager_ids = self._find_managers()
            if manager_ids:
                self.sudo().write({'state': self.TO_APPROVE, 'osoba_priradena_ids': [(6,0,manager_ids.ids)], 'manager_ids': [(6,0,manager_ids.ids)], 'wf_dovod': ''})
                # Nemozem pouzit current-user, pretoze mail sa posiela cez konto Admina!!!
                self.sudo().send_mail(manager_ids)
            else:
                _logger.debug("no managers found")
                raise UserError('No manager(s) found to assign.')

        # Manager schvalil
        elif self.env.user.partner_id.id in self.manager_ids.ids:
            if self.is_user_assigned:
                _logger.debug("Manager '" + self.env.user.partner_id.display_name + "' approved")
                self.sudo().write({'osoba_priradena_ids': [(3,self.env.user.partner_id.id)], 'wf_dovod': ''})

                # posleme email PC, aby vedel, ze manager schvalil
                context = {'manager_name': self.env.user.partner_id.display_name}
                self.sudo().send_mail([self.pc_id], template_name='mail_cp_manager_approved', context=context)

        # aktualny uzivatel je medzi priradenymi managermi
        if self.env.user.partner_id.id in self.manager_ids.ids:
            # vsetci managery schvalili
            if not self.osoba_priradena_ids.ids:
                _logger.debug("ALL managers approved")
                self.sudo().write({'state': self.APPROVED, 'osoba_priradena_ids': [(5)], 'wf_dovod': ''})
                self.sudo().send_mail([self.dodavatel_id, self.pc_id], template_name='mail_cp_approved')
                self.sudo().action_exportSAP()


        return True

    @api.one
    def wf_not_complete(self):
        _logger.debug("workflow action to NOT_COMPLETE")
        self.ensure_one()

        self.wf_can_user_workflow()

        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.pc_id.id in self.osoba_priradena_ids.ids:
            _logger.debug("workflow action to IN_PROGRESS")
            self.sudo().write({'state': self.IN_PROGRESS, 'osoba_priradena_ids': [(6,0,[self.dodavatel_id.id])], 'wf_dovod': ''})
            self.sudo().send_mail([self.dodavatel_id])
            self.sudo().signal_workflow('not_complete')
            # call WF: signal "not complete". som v stave "to_approve". potrebujem ist do in_progers

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.pm_id.id in self.osoba_priradena_ids.ids:
            _logger.debug("workflow action to TO_APPROVE")
            self.sudo().write({'state': self.TO_APPROVE, 'osoba_priradena_ids': [(6,0,[self.pc_id.id])], 'wf_dovod': ''})
            self.sudo().send_mail([self.pc_id])

        return True

    @api.one
    def wf_cancel(self):
        _logger.debug("workflow action to CANCEL")
        self.ensure_one()

        if self.wf_dovod:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.wf_dovod + "</li></ul>")

        self.sudo().write({'state': self.CANCEL, 'osoba_priradena_ids': [(5)], 'wf_dovod': ''})
        self.sudo().send_mail([self.dodavatel_id, self.pc_id], template_name='mail_cp_canceled')
        return True

    @api.one
    def send_mail(self, partner_ids=None, template_name='mail_cp_assigned', context=None):

        _logger.debug("send mail to " + str(partner_ids))

        # Find the e-mail template
        # definovane vo views/mail_template.xml
        template = self.env.ref('o2net.' + template_name)
        if not template:
            _logger.debug("unable send mail. template not found. template_name: " + str(template_name))
            return

        templateObj = self.env['mail.template'].browse(template.id)

        admin = self.env['res.users'].browse(SUPERUSER_ID)
        if admin:
            _logger.debug("admin mail: " + admin.partner_id.email)
            templateObj.email_from = admin.partner_id.email

        if partner_ids:
            emails = []
            partners = []
            for partner in partner_ids:
                emails.append(partner.email)
                partners.append(str(partner.id))

            templateObj.email_to = ",".join(emails)
            templateObj.partner_to = ",".join(partners)
            templateObj.lang = self.env.user.partner_id.lang


        if context is None:
            _logger.debug('send mail without context')
            mail_id = templateObj.send_mail(self.id, force_send=True, raise_exception=False)
        else:
            _logger.debug('send mail using context: ' + str(context))
            mail_id = templateObj.with_context(context).send_mail(self.id, force_send=True, raise_exception=False)
