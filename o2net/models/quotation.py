# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp import http
import datetime
import logging
import base64

_logger = logging.getLogger(__name__)

class Quotation(models.Model):
    _name = 'o2net.quotation'
    _description = "o2net - Quotation"
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
        mail_ids = self.env['mail.mail'].search([('', '=', partner_id)], order = "po_total_price_limit desc", limit=1)

        return ret;

    @api.one
    def action_exportSAP(self):
        export_file_name = 'sap_export_' + self.project_number + '_' + str(datetime.date.today()) + '.txt'
        self.sap_export_file_name = export_file_name
        self.sap_export_content = self._get_sap_export_content()
        self.sap_export_file_binary = base64.encodestring(self.sap_export_content)
        self.message_post(body='<ul class ="o_mail_thread_message_tracking"><li>' + 'Subor "' + export_file_name + '" pre SAP bol vygenerovany' + "</li></ul>")

    @api.multi
    def _get_sap_export_content(self):
        data = []
        if self.project_number:
            data.append('[PSPID]' + chr(9) + self.project_number)
        if self.pc_id.code:
            data.append('[WEMPF]'+chr(9)+self.pc_id.code)
        else:
            data.append('[WEMPF]' + chr(9) + '???')
        if self.vendor_id.code:
            data.append('[MSTRT]' + chr(9) + self.vendor_id.code)
        if self.end_date:
            dt_obj = datetime.datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT)
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
                        zdroj.project_number,
                        CHR(9),
                        case
                            when zdroj.druh = '1T' then
                                concat(q.project_number, '.', s.name)
                            when zdroj.druh = '2A' then
                                concat(q.project_number, '.', s.name)
                        else
                            q.project_number
                        end,
                        CHR(9),
                        to_char(q.end_date, 'DD.MM.YYYY')) as vystup
                    from
                        (   select
                                '1T' as druh,
                         		max(p.intern_code) as kod,
                                sum(total_price) as project_number,
                                p.section_id as section_id,
                                max(qi.quotation_id) as quotation_id
                            from o2net_quotation_item qi
                            join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                            join o2net_product p on pi.item_id = p.id
                            where
                               qi.quotation_id = %s
                               and p.is_package = false
                            group by p.section_id,p.intern_code
                            union
                         	select
                         		'2A',
                         		(select atypservice from o2net_section where id = atyp.section_id),
                         		sum(price),
                          		atyp.section_id,
                                max(atyp.quotation_id)
                            from o2net_quotation_item_atyp atyp
                            where atyp.quotation_id = %s
                            group by atyp.section_id
                         	union
                            select
                                '3B',
                                p.code,
                                qip.quantity,
                                p.section_id,
                                qip.quotation_id
                            from o2net_quotation_item_package qip
                            join o2net_pricelist_item cp on qip.pricelist_item_id = cp.id
                            join o2net_product p on cp.item_id = p.id
                            where
                                qip.quotation_id = %s
                                and p.is_package = true

                        ) zdroj
                     join
                        o2net_section s on zdroj.section_id = s.id
                    join
                        o2net_quotation q on zdroj.quotation_id = q.id
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

    @api.depends('quotation_item_ids.total_price','quotation_item_package_ids.total_price','quotation_item_atyp_ids.price')
    def _compute_amount_all(self):
        for cp in self:
            cp_total_price = 0.0
            for line in cp.quotation_item_ids:
                cp_total_price += line.total_price

            for line in cp.quotation_item_package_ids:
                cp_total_price += line.total_price

            for lineAtyp in cp.quotation_item_atyp_ids:
                cp_total_price += lineAtyp.price

            cp.update({'total_price': cp_total_price})

    @api.one
    @api.depends('vendor_id','assigned_persons_ids')
    def _compute_ro_datumoddo(self):
        if self.assigned_persons_ids:
            self.ro_datumoddo = not self.vendor_id.id in self.assigned_persons_ids.ids

    def _compute_is_user_assigned(self):
        ret = self.env.user.partner_id.id in self.assigned_persons_ids.ids
        self.is_user_assigned = ret
        return ret

    @api.depends('assigned_persons_ids')
    def _compute_can_user_exec_wf(self):
        ret = self.is_user_assigned or self.env.user.id == SUPERUSER_ID
        return ret

    @api.one
    def _compute_record_url(self):
        base = self.env['ir.config_parameter'].get_param('web.base.url')
        id = self.id
        ir_model_data = self.env['ir.model.data']
        menu_id = ir_model_data.get_object_reference('o2net', 'menu_quotation_preview')[1]
        action_id = ir_model_data.get_object_reference('o2net', 'action_window_qout_preview')[1]
        url = "%s/web#id=%s&view_type=form&model=o2net.quotation&menu_id=%s&action=%s" % (base, id, menu_id, action_id)
        _logger.debug("URL: " + url)
        self.base_url = url

    @api.one
    def _get_section(self, cp_id):
        data = []

        query = """select zdroj.id as id, zdroj.section as section
                            from
                            (
                                select s.ID as id,s.name as section
                                from o2net_quotation_item qi
                                join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                                join o2net_product p on pi.item_id = p.id and p.is_package = false
                                join o2net_section s on p.section_id = s.id
                                where qi.quotation_id = %s
                                union all
                                select s.ID, s.name
                                from o2net_quotation_item_atyp qia
                                join o2net_section s on qia.section_id = s.id
                                where qia.quotation_id = %s
                            ) zdroj
                            group by zdroj.id, zdroj.section
                            order by zdroj.section;"""

        self.env.cr.execute(query, (cp_id,cp_id))
        data = self.env.cr.dictfetchall()

        if data:
            return data
        else:
            return {}

    @api.one
    def _get_rows_section_typ(self, cp_id, oddiel_id):
        data = []

        query = """ select  qi.quotation_id as quotation_id,
                            s.name as section,
                            p.intern_code as ksz,
                            p.name as item,
                            p.unit_of_measure as uom,
                            qi.quantity as pocet,
                            qi.unit_price as unit_price,
                            qi.total_price as total_price
                    from o2net_quotation_item qi
                        join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                        join o2net_product p on pi.item_id = p.id and p.is_package = false
                        join o2net_section s on p.section_id = s.id
                    where qi.quotation_id = %s
                        and s.id = %s;"""

        self.env.cr.execute(query, (cp_id, oddiel_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_rows_section_atyp(self, cp_id, oddiel_id):
        data = []
        _logger.debug("_get_rows_oddiel_atyp " + str(cp_id) + ", " + str(oddiel_id))

        query = """ select  cppa.cenova_ponuka_id as cp_id,
                            o.name as oddiel,
                            cppa.name as polozka,
                            cppa.price as price_celkom
                    from o2net_cenova_ponuka_polozka_atyp cppa
                    join o2net_oddiel o on cppa.oddiel_id = o.id
                    where cppa.cenova_ponuka_id = %s
                        and o.id = %s;"""

        self.env.cr.execute(query, (cp_id, oddiel_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_rows_section_package(self, quotation_id):
        data = []

        query = """select   qip.quotation_id as quotation_id,
                            s.name as section,
                            p.code as code,
                            p.name as item,
                            p.unit_of_measure as uom,
                            qip.unit_price as unit_price,
                            qip.quantity as quantity,
                            qip.total_price as total_price
                    from o2net_quotation_item_package qip
                            join o2net_pricelist_item pi on qip.pricelist_item_id = pi.id
                            join o2net_product p on pi.item_id = p.id and p.is_package = true
                            join o2net_section s on p.section_id = s.id
                        where qip.quotation_id = %s;"""

        self.env.cr.execute(query, ([quotation_id]))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_price_section(self, quotation_id, section_id):
    # -------------------------------------------------------------
    # celkova price pre cenovu ponuku a oddiel
    # pocitaju sa polozky typove a atypove spolu podla oddielu
    # -------------------------------------------------------------

        price = 0
        _logger.debug("_get_price_oddiel cp_id=" + str(quotation_id) + " oodiel_id=" + str(section_id))

        query = """select sum(zdroj.price)
                    from
                    (   select sum(cppa.price) as price
                        from o2net_cenova_ponuka cp
                        join o2net_cenova_ponuka_polozka_atyp cppa on cp.id = cppa.cenova_ponuka_id
                        join o2net_oddiel o on cppa.oddiel_id = o.id
                        where cp.id = %s
                        and o.id = %s
                        union all
                        select sum(cpp.price_celkom)
                        from o2net_cenova_ponuka cp
                        join o2net_cenova_ponuka_polozka cpp on cp.id = cpp.cenova_ponuka_id
                        join o2net_cennik_polozka c on cpp.cennik_polozka_id = c.id
                        join o2net_polozka p on c.polozka_id = p.id
                        where cp.id = %s
                        and p.oddiel_id = %s
                        and p.is_balicek = false ) zdroj;"""

        self.env.cr.execute(query, (quotation_id, section_id, quotation_id, section_id))
        price = self.env.cr.fetchone()[0]
        _logger.debug("_get_price_oddiel price=" + str(price))

        return price

    @api.one
    def _get_price_section_atyp(self, quotation_id, section_id, atyp):
    # --------------------------------------------------------------------------
    # total price
    # --------------------------------------------------------------------------
        price = 0
        _logger.debug("_get_price_oddiel_atyp cp_id=" + str(quotation_id) + " oodiel_id=" + str(section_id) + " atyp=" + str(atyp))

        if atyp==1:
            query = """select sum(qia.price)
                        from o2net_quotation q
                        join o2net_quotation_item_atyp qia on q.id = qia.quotation_id
                        join o2net_section s on qia.section_id = s.id
                        where
                            q.id = %s
                            and s.id = %s;"""

            self.env.cr.execute(query, (quotation_id, section_id))
            price = self.env.cr.fetchone()[0]

        if atyp==0:
            query = """select sum(qi.total_price)
                        from o2net_quotation q
                        join o2net_quotation_item qi on q.id = qi.quotation_id
                        join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                        join o2net_product p on pi.item_id = p.id
                        where q.id = %s
                        and p.section_id = %s
                        and p.is_package = false;"""

            self.env.cr.execute(query, (quotation_id, section_id))
            price = self.env.cr.fetchone()[0]

        return price

    @api.one
    def _get_price_packages(self, quotation_id):
    # ---------------------------------------------
    # total price for quotation and packages
    # ---------------------------------------------
        price = 0
        _logger.debug("_get_price_balicky cp_id=" + str(quotation_id))

        query = """select sum(qip.total_price)
                    from o2net_quotation q
                    join o2net_quotation_item_package qip on q.id = qip.quotation_id
                    join o2net_pricelist_item pli on qip.pricelist_item_id = pli.id
                    join o2net_product p on pli.item_id = p.id
                    where q.id = %s
                    and p.is_package = true;"""

        self.env.cr.execute(query, ([quotation_id]))
        price = self.env.cr.fetchone()[0]
        return price

    @api.one
    def _get_rows(self, cp_id):
        data = []
        _logger.debug("a_function_name " + str(cp_id))

        query = """ select  typorder as typorder,
                            typ as typ,
                            sectiontyp as sectiontyp,
                            q.id as id,
                            zdroj.section as section,
                            ksz as ksz,
                            item as item,
                            zdroj.unit_price as unit_price,
                            zdroj.uom as uom,
                            quantity as quantity,
                            zdroj.total_price as total_price,
                            q.project_number as project_number
                            from
                            (
                            select  '1t' as typorder,
                                    't' as typ,
                                    concat(s.name,'p') as sectiontyp,
                                    qi.quotation_id as quotation_id,
                                    s.name as section,
                                    p.intern_code as ksz,
                                    p.name as item,
                                    qi.unit_price as unit_price,
                                    p.unit_of_measure as uom,
                                    qi.quantity as quantity,
                                    qi.total_price as total_price
                            from o2net_quotation_item qi
                            join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                            join o2net_product p on pi.item_id = p.id and p.is_package = false
                            join o2net_section s on p.section_id = s.id
                            where qi.quotation_id = %s
                            union all
                            select  '2a',
                                    'a',
                                    concat(s.name,'p'),
                                    qia.quotation_id,
                                    s.name,
                                    '',
                                    qia.name,
                                    null,
                                    null,
                                    null,
                                    qia.price
                            from o2net_quotation_item_atyp qia
                            join o2net_section s on qia.section_id = s.id
                            where qia.quotation_id = %s
                            union all
                            select  '3b',
                                    'b',
                                    concat(s.name,'b'),
                                    qip.quotation_id,
                                    s.name,
                                    p.code,
                                    p.name,
                                    qip.unit_price,
                                    p.unit_of_measure,
                                    qip.quantity,
                                    qip.total_price
                            from o2net_quotation_item_package qip
                            join o2net_pricelist_item pi on qip.pricelist_item_id = pi.id
                            join o2net_product p on pi.item_id = p.id and p.is_package = true
                            join o2net_section s on p.section_id = s.id
                            where qip.quotation_id = %s
                            ) zdroj
                            join o2net_quotation q on zdroj.quotation_id = q.id order by typorder;"""

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

    # FIELDS
    # computed fields
    ro_datumoddo = fields.Boolean(string="RO date From To", compute=_compute_ro_datumoddo, store=False, copy=False)
    can_user_exec_wf = fields.Boolean(string="Can user execute workflow action", compute=_compute_can_user_exec_wf, store=False, copy=False)
    is_user_assigned = fields.Boolean(string="Is current user assigned", compute=_compute_is_user_assigned)

    name = fields.Char(required=True, string="Name", size=50, copy=True)
    project_number = fields.Char(string="Project number (PSID)", required=True, copy=True);
    financial_code = fields.Char(string="Financial code", size=10, required=True, copy=True)
    shortname = fields.Char(string="Short name", required=True, copy=True)
    start_date = fields.Date(string="Start date", default=datetime.date.today(), copy=False);
    end_date = fields.Date(string="End date", copy=False);
    note = fields.Text(string="Note", track_visibility='onchange', copy=False)
    workflow_reason = fields.Text(string='Workflow reason', copy=False, help='Enter workflow reason mainly for actions "Return for repair" and "Cancel"')
    total_price = fields.Float(compute=_compute_amount_all, string='Total price', store=True, digits=(10, 2), track_visibility='onchange', copy=False)
    vendor_id = fields.Many2one('res.partner', required=True, string='Vendor', track_visibility='onchange', domain=partners_in_group_supplier, copy=True)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc, copy=True, default=lambda self: self._get_default_pc())
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm, copy=True)
    manager_ids = fields.Many2many('res.partner', relation="o2net_quotation_manager_rel", string='Manager', domain=partners_in_group_manager, copy=False)
    assigned_persons_ids = fields.Many2many('res.partner', relation="o2net_qoutation_assigned_rel", string='Assigned persons', copy=False, default = lambda self: [(4, self.env.user.partner_id.id)])

    state = fields.Selection(State, string='State', readonly=True, default='draft', track_visibility='onchange', copy=False)
    state_date = fields.Date(string="date state", default=datetime.date.today(), copy=False);
    price_list_id = fields.Many2one('o2net.pricelist', string='Price list', copy=True)
    currency_id = fields.Many2one(related='price_list_id.currency_id', string="Currency", copy=True)

    quotation_item_ids = fields.One2many('o2net.quotation.item', 'quotation_id', string='Items', track_visibility='onchange', copy=True)
    quotation_item_package_ids = fields.One2many('o2net.quotation.item_package', 'quotation_id', string='Packages', track_visibility='onchange', copy=True)
    quotation_item_atyp_ids = fields.One2many('o2net.quotation.item_atyp', 'quotation_id', string='Atypical items', track_visibility='onchange', copy=True)

    sap_export_content = fields.Text(string="Export for SAP", default='ABCDEFGH', copy=False)
    sap_export_file_name = fields.Char(string="Export file name", copy=False)
    sap_export_file_binary = fields.Binary(string='Export file', copy=False)

    base_url = fields.Char(compute=_compute_record_url, string="Link", store=False, copy=False, )

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # log changes in Quotation's items
        if 'quotation_item_ids' in vals:
            record_history_tmpl = "<li><b>%s</b> %s</li>"
            msg = ""
            for record in vals.get('quotation_item_ids'):
                _logger.debug("record " + str(record))
                action_id = record[0]
                if action_id == 0:
                    id = record[2].get('pricelist_item_id')
                    name = self.env['o2net.pricelist.item'].browse(id).name
                    msg += record_history_tmpl % ('+++', name)
                elif action_id == 2:
                    id = record[1]
                    name = self.env['o2net.quotation.item'].browse(id).name
                    msg += record_history_tmpl % ('---', name)

            self.message_post(body="<ul class =""o_mail_thread_message_tracking"">%s</ul>" % msg, message_type="notification")

        res = super(Quotation, self).write(vals)

        # ak zapisujeme stav prisli sme sem z WF akcie, a preto koncime. automaticka zmena stavu WF je len v pripade akcie SAVE kde sa 'state' nemeni!
        if not vals.get('state') == None:
            return res

        # ak je prihlaseny Dodavatel, je mu priradena CP a je v stave ASSIGNED tak pri save zmenime stav na IN_PROGRESS
        if self.vendor_id.id in self.assigned_persons_ids.ids:
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
        new_cp = super(Quotation, self).copy(default=default)

        return new_cp

    @api.multi
    def unlink(self):
        # cenova ponuka moze byt zmazane len v stave "DRAFT". potom je mozne ju zrusit cez WF akciu "Cancel"
        if not self.state == self.DRAFT:
            raise AccessError("Cenovú ponuku je možné zmazať len pokiaľ je v stave 'Návrh'. V ostatnom prípade použite workflow akciu 'Zrušiť'")

    @api.onchange('vendor_id')
    def _find_cennik(self):
        result = {}
        if not self.vendor_id:
            return result

        _logger.debug("Looking for supplier's valid pricelist " + str(self.vendor_id.name))
        cennik_ids = self.env['o2net.pricelist'].search([('vendor_id', '=', self.vendor_id.id),
                                                         ('valid_from', '<=', datetime.date.today()),
                                                         ('valid_to', '>', datetime.date.today())], limit = 1)

        for rec in cennik_ids:
            _logger.debug(rec.name)

        if cennik_ids:
            self.price_list_id = cennik_ids[0]
        else:
            self.price_list_id = ''

        # pri zmene dodavatela a tym padol aj cennika zmaz vsetky polozky
        self.quotation_item_ids = None;

        result = {'price_list_id': self.price_list_id}
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
    # najdi partnera v skupine 'Manager', ktoreho field 'price_na_schvalenie' je vacsia ako celkova price CP
    def _find_managers(self):
        _logger.debug("Looking for manager to approve order of price " + str(self.total_price))
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        manager_ids = self.env['res.partner'].search([('id', 'in', partner_ids),('po_total_price_limit', '<=', self.total_price)], order = "cp_total_price_limit desc")

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
        if self.vendor_id is False:
            raise AccessError(_("Quotation does not have vendor assigned"))

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
        if self.workflow_reason:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.workflow_reason + "</li></ul>")

        self.sudo().write({'state': self.ASSIGNED, 'assigned_persons_ids': [(6,0,[self.vendor_id.id])], 'workflow_reason': ''})
        self.sudo().send_mail([self.vendor_id])
        return True

    @api.one
    def wf_in_progress(self):
        _logger.debug("workflow action to IN_PROGRESS")
        self.ensure_one()
        if self.workflow_reason:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.workflow_reason + "</li></ul>")

        self.sudo().write({'state': self.IN_PROGRESS, 'assigned_persons_ids': [(6,0,[self.vendor_id.id])], 'workflow_reason': ''})
        # notify PC via email that supplier starts working on CP
        self.sudo().send_mail([self.pc_id], template_name='mail_cp_in_progress')
        return True

    @api.one
    def wf_approve(self):
        self.ensure_one()
        _logger.debug("workflow action to APPROVE")

        # do historie pridame 'workflow_reason'
        if self.workflow_reason:
            # add to tracking values
            self.message_post(body='<ul class="o_mail_thread_message_tracking"><li>Workflow reason: ' + self.workflow_reason + '</li></ul>')

        # Dodavatel poslal na schvalenie PC
        if self.vendor_id.id in self.assigned_persons_ids.ids:
            _logger.debug("Supplier sent to approve by PC")
            self.sudo().write({'state': self.TO_APPROVE, 'assigned_persons_ids': [(6,0,[self.pc_id.id])], 'workflow_reason': ''})
            self.sudo().send_mail([self.pc_id])

        # PC poslal na schvalenie PM
        elif self.pc_id.id in self.assigned_persons_ids.ids:
            _logger.debug("PC sent to approve by PM")
            self.sudo().write({'state': self.TO_APPROVE, 'assigned_persons_ids': [(6,0,[self.pm_id.id])], 'workflow_reason': ''})
            self.sudo().send_mail([self.pm_id])

        # PM poslal na schvalenie Managerovy
        elif self.pm_id.id in self.assigned_persons_ids.ids:
            _logger.debug("PM sent to approve by Manager")
            manager_ids = self._find_managers()
            if manager_ids:
                self.sudo().write({'state': self.TO_APPROVE, 'assigned_persons_ids': [(6,0,manager_ids.ids)], 'manager_ids': [(6,0,manager_ids.ids)], 'wf_dovod': ''})
                # Nemozem pouzit current-user, pretoze mail sa posiela cez konto Admina!!!
                self.sudo().send_mail(manager_ids)
            else:
                _logger.debug("no managers found")
                raise UserError('No manager(s) found to assign.')

        # Manager schvalil
        elif self.env.user.partner_id.id in self.manager_ids.ids:
            if self.is_user_assigned:
                _logger.debug("Manager '" + self.env.user.partner_id.display_name + "' approved")
                self.sudo().write({'assigned_persons_ids': [(3,self.env.user.partner_id.id)], 'workflow_reason': ''})

                # posleme email PC, aby vedel, ze manager schvalil
                context = {'manager_name': self.env.user.partner_id.display_name}
                self.sudo().send_mail([self.pc_id], template_name='mail_cp_manager_approved', context=context)

        # aktualny uzivatel je medzi priradenymi managermi
        if self.env.user.partner_id.id in self.manager_ids.ids:
            # vsetci managery schvalili
            if not self.assigned_persons_ids.ids:
                _logger.debug("ALL managers approved")
                self.sudo().write({'state': self.APPROVED, 'assigned_persons_ids': [(5)], 'workflow_reason': ''})
                self.sudo().send_mail([self.vendor_id, self.pc_id], template_name='mail_cp_approved')
                self.sudo().action_exportSAP()


        return True

    @api.one
    def wf_not_complete(self):
        _logger.debug("workflow action to NOT_COMPLETE")
        self.ensure_one()

        self.wf_can_user_workflow()

        if self.workflow_reason:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.workflow_reason + "</li></ul>")

        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.pc_id.id in self.assigned_persons_ids.ids:
            _logger.debug("workflow action to IN_PROGRESS")
            self.sudo().write({'state': self.IN_PROGRESS, 'assigned_persons_ids': [(6,0,[self.vendor_id.id])], 'workflow_reason': ''})
            self.sudo().send_mail([self.vendor_id])
            self.sudo().signal_workflow('not_complete')
            # call WF: signal "not complete". som v stave "to_approve". potrebujem ist do in_progers

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.pm_id.id in self.assigned_persons_ids.ids:
            _logger.debug("workflow action to TO_APPROVE")
            self.sudo().write({'state': self.TO_APPROVE, 'assigned_persons_ids': [(6,0,[self.pc_id.id])], 'workflow_reason': ''})
            self.sudo().send_mail([self.pc_id])

        return True

    @api.one
    def wf_cancel(self):
        _logger.debug("workflow action to CANCEL")
        self.ensure_one()

        if self.workflow_reason:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.workflow_reason + "</li></ul>")

        self.sudo().write({'state': self.CANCEL, 'assigned_persons_ids': [(5)], 'workflow_reason': ''})
        self.sudo().send_mail([self.vendor_id, self.pc_id], template_name='mail_cp_canceled')
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
