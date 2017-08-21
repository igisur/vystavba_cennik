# -*- coding: utf-8 -*-

import base64
import datetime
import logging

from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class Quotation(models.Model):
    _name = 'o2net.quotation'
    _description = "o2net - Quotation"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    DRAFT = 'draft'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    TO_APPROVE = 'to_approve'
    APPROVE = 'approve'
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

    GROUP_SUPPLIER = 'o2net.group_vendor'
    GROUP_PC = 'o2net.group_pc'
    GROUP_PM = 'o2net.group_pm'
    GROUP_MANAGER = 'o2net.group_manager'
    GROUP_ADMIN = 'o2net.group_admin'

    @api.model
    def do_check_approve(self):
        # validation of waiting for till Quotation is approved
        # called from cron
        today = datetime.datetime.now()
        schvalene = self.search([('state', '=', 'to_approve')])
        for row in schvalene:
            if not row.manager_ids:
                continue

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
                if rozdiel > manager.reminder_interval:
                    # send mail
                    self.send_mail([manager], template_name='mail_manager_warning')

    def get_last_mail_date(self, partner_id):
        ret = {}
        # looking for the last mail sent to partner
        mail_ids = self.env['mail.mail'].search([('', '=', partner_id)], order="po_total_price_limit desc", limit=1)
        return ret;

    @api.one
    def action_exportSAP(self):
        export_file_name = self.shortname + '_' + self.project_number + '_' + str(datetime.date.today()) + '.txt'
        self.sap_export_file_name = export_file_name
        self.sap_export_content = self._get_sap_export_content()
        self.sap_export_file_binary = base64.encodestring(self.sap_export_content)
        self.message_post(
            body='<ul class ="o_mail_thread_message_tracking"><li>' + 'Subor "' + export_file_name + '" pre SAP bol vygenerovany' + "</li></ul>")

    @api.one
    def _format_number(self, number4formating, currency=[]):
        formatNumber = 0;

        if number4formating:
            formatNumber = "{0:,.2f}".format(number4formating).replace(',', ' ').replace('.',',');

            if currency:
                formatNumber = formatNumber + " " + self.currency_id.symbol;

        return formatNumber;

    @api.multi
    def _get_sap_export_content(self):
        data = []
        if self.project_number:
            data.append('[PSPID]' + chr(9) + self.project_number)
        if self.pc_id.code:
            data.append('[WEMPF]' + chr(9) + self.pc_id.code)
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
                        replace(to_char(zdroj.project_number,'9999999999990D00'), '.', ','),
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
                     left join
                        o2net_section s on zdroj.section_id = s.id
                    join
                        o2net_quotation q on zdroj.quotation_id = q.id
                    order by zdroj.druh;"""

        self.env.cr.execute(query, (self.id, self.id, self.id))
        fetchrows = self.env.cr.dictfetchall()

        for row in fetchrows:
            data.append(row.get('vystup').decode('utf8'))
        ret = '\r\n'.join(data)
        return ret

    # limit partners to specific group
    @api.model
    def _partners_in_group(self, group_name):
        group = self.sudo().env.ref(group_name)
        _logger.debug('Group: ' + group.name.encode('ascii','ignore'))
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

    def partners_in_group_pc(self):
        partner_ids = self._partners_in_group(self.GROUP_PC)
        return [('id', 'in', partner_ids)]

    def partners_in_group_pm(self):
        partner_ids = self._partners_in_group(self.GROUP_PM)
        return [('id', 'in', partner_ids)]

    def partners_in_group_manager(self):
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        return [('id', 'in', partner_ids)]

    @api.depends('quotation_item_ids.total_price', 'quotation_item_package_ids.total_price',
                 'quotation_item_atyp_ids.price')
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
    @api.depends('vendor_id', 'assigned_persons_ids')
    def _compute_ro_datumoddo(self):
        if self.assigned_persons_ids:
            self.ro_datumoddo = not self.vendor_id.id in self.assigned_persons_ids.ids

    @api.depends('assigned_persons_ids')
    def _compute_is_user_assigned(self):
        # check if logged user is VENDOR EMPLOYEE
        if self.env.user.partner_id.parent_id:
            ret = self.env.user.partner_id.parent_id.id in self.assigned_persons_ids.ids
        else:
            ret = self.env.user.partner_id.id in self.assigned_persons_ids.ids

        self.is_user_assigned = ret
        return ret

    def _search_user_assigned(self, operator, value):
        _logger.debug('_search_user_assigned ' + str(operator) + '\'' + str(value) + '\'')

        if self.env.user.partner_id.parent_id:
            partner_id = self.env.user.partner_id.parent_id.id
        else:
            partner_id = self.env.user.partner_id.id

        if value == "True" and operator == '=':
            _logger.debug('partner_id:' + str(partner_id))
            return [('assigned_persons_ids', 'in', [partner_id])]
        else:
            return []

    @api.depends('assigned_persons_ids')
    def _compute_can_user_exec_wf(self):
        ret = self.is_user_assigned or self.env.user.id == SUPERUSER_ID or self.env.user.has_group(self.GROUP_ADMIN)
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
    def _get_section(self, quotation_id):
        data = []
        _logger.debug("_get_section " + str(quotation_id))
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

        self.env.cr.execute(query, (quotation_id, quotation_id))
        data = self.env.cr.dictfetchall()

        if data:
            return data
        else:
            return {}

    @api.one
    def _get_rows_section_typ(self, quotation_id, section_id):
        data = []

        query = """ select  qi.quotation_id as quotation_id,
                            s.name as section,
                            p.intern_code as ksz,
                            p.name as item,
                            p.unit_of_measure as uom,
                            qi.quantity as quantity,
                            qi.unit_price as unit_price,
                            qi.total_price as total_price
                    from o2net_quotation_item qi
                        join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                        join o2net_product p on pi.item_id = p.id and p.is_package = false
                        join o2net_section s on p.section_id = s.id
                    where qi.quotation_id = %s
                        and s.id = %s;"""

        self.env.cr.execute(query, (quotation_id, section_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_rows_section_atyp(self, quotation_id, section_id):
        data = []
        _logger.debug("_get_rows_section_atyp " + str(quotation_id) + ", " + str(section_id))

        query = """ select  qia.quotation_id as quotation_id,
                            s.name as section,
                            qia.name as item,
                            qia.price as total_price
                    from o2net_quotation_item_atyp qia
                    join o2net_section s on qia.section_id = s.id
                    where qia.quotation_id = %s
                        and s.id = %s;"""

        self.env.cr.execute(query, (quotation_id, section_id))
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
                            left join o2net_section s on p.section_id = s.id
                        where qip.quotation_id = %s;"""

        self.env.cr.execute(query, ([quotation_id]))
        data = self.env.cr.dictfetchall()
        return data

    @api.one
    def _get_price_section(self, quotation_id, section_id):
        price = 0
        query = """select sum(zdroj.price)
                    from
                    (   select sum(qia.price) as price
                        from o2net_quotation q
                        join o2net_quotation_item_atyp qia on q.id = qia.quotation_id
                        join o2net_section s on qia.section_id = s.id
                        where q.id = %s
                        and s.id = %s
                        union all
                        select sum(qi.total_price)
                        from o2net_quotation q
                        join o2net_quotation_item qi on q.id = qi.quotation_id
                        join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                        join o2net_product p on pi.item_id = p.id
                        where q.id = %s
                        and p.section_id = %s
                        and p.is_package = false ) zdroj;"""

        self.env.cr.execute(query, (quotation_id, section_id, quotation_id, section_id))
        price = self.env.cr.fetchone()[0]

        return price

    @api.one
    def _get_price_section_atyp(self, quotation_id, section_id, atyp):
    # --------------------------------------------------------------------------
    # total price
    # --------------------------------------------------------------------------
        price = 0
        _logger.debug(
            "_get_price_oddiel_atyp cp_id=" + str(quotation_id) + " oodiel_id=" + str(section_id) + " atyp=" + str(
                atyp))

        if atyp == 1:
            query = """select sum(qia.price)
                        from o2net_quotation q
                        join o2net_quotation_item_atyp qia on q.id = qia.quotation_id
                        join o2net_section s on qia.section_id = s.id
                        where
                            q.id = %s
                            and s.id = %s;"""

            self.env.cr.execute(query, (quotation_id, section_id))
            price = self.env.cr.fetchone()[0]

        if atyp == 0:
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
    def _get_price_items(self, quotation_id):
    # ---------------------------------------------
    # total price for items quotation (typical and non typical)
    # ---------------------------------------------
        price = 0
        _logger.debug("_get_price_items id=" + str(quotation_id))

        query = """select sum(zdroj.price)
                    from (
                            select sum(qia.price) as price
                             from o2net_quotation q
                             join o2net_quotation_item_atyp qia on q.id = qia.quotation_id
                             left join o2net_section s on qia.section_id = s.id
                             where q.id = %s
                            union
                            select sum(qi.total_price)
                             from o2net_quotation q
                             join o2net_quotation_item qi on q.id = qi.quotation_id
                             join o2net_pricelist_item pi on qi.pricelist_item_id = pi.id
                             join o2net_product p on pi.item_id = p.id
                             where q.id = %s
                                   and p.is_package = false
                          ) zdroj;"""

        self.env.cr.execute(query, (quotation_id, quotation_id))
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
                            left join o2net_section s on p.section_id = s.id
                            where qip.quotation_id = %s
                            ) zdroj
                            join o2net_quotation q on zdroj.quotation_id = q.id order by typorder;"""

        self.env.cr.execute(query, (cp_id, cp_id, cp_id))
        data = self.env.cr.dictfetchall()
        return data

    @api.model
    def _get_default_vendor(self):
        _logger.debug('_get_default_vendor')
        ret = None

    @api.model
    def _get_default_pc(self):
        _logger.debug('_get_default_pc')
        partners = self._partners_in_group(self.GROUP_PC)
        _logger.debug('partners: ' + str(partners))

        ret = None
        if self.env.user.partner_id.id in partners:
            _logger.debug('current user is PC. will be used as default PC.')
            ret = self.env.user.partner_id.id

        return ret

    @api.model
    def _get_default_assigned(self):
        _logger.debug('_get_default_assigned')
        ret = []
        partners = self._partners_in_group(self.GROUP_SUPPLIER)
        if self.env.user.partner_id.id in partners:
            if self.env.user.partner_id.parent_id:
                ret.append(self.env.user.partner_id.parent_id.id)
            else:
                _logger.debug('logged as VENDOR COMPANY OR IS NOT ASSIGNED TO COMPANY?' + str(self.env.user))
                ret.append(self.env.user.partner_id.id)
        else:
            ret.append(self.env.user.partner_id.id)

        return ret

    @api.multi
    def _compute_duplicate_quots(self):
        _logger.debug('_compute_duplicate_quots')

        quots = self.env['o2net.quotation']
        for rec in self:
            _logger.debug("ID: %s, financial_code: %s" % (rec.id, rec.financial_code))
            if rec.financial_code:
                rec.duplicate_quots = quots.search_count([('financial_code', '=', rec.financial_code),('id', '<>', rec.id)])

    @api.multi
    def action_duplicates(self):
        _logger.debug('action_duplicates')

        if not self.duplicate_quots:
            return False

        tree_view = self.env.ref('o2net.view_tree_quotation_duplicates')
        _logger.debug('o2net.view_tree_quotation_duplicates:' + str(tree_view.id))

        return {
            "type": "ir.actions.act_window",
            "name": "Duplicate quotations",
            "res_model": "o2net.quotation",
            "views": [[tree_view.id, "tree"]],
            "domain": [["financial_code", "=", self.financial_code], ["id", "<>", self.id]],
            "target": "new"
        }


    # FIELDS
    # computed fields
    ro_datumoddo = fields.Boolean(string="RO date From To", compute=_compute_ro_datumoddo, store=False, copy=False)
    can_user_exec_wf = fields.Boolean(string="Can user execute workflow action", compute=_compute_can_user_exec_wf, store=False, copy=False)
    is_user_assigned = fields.Boolean(string="Is current user assigned", compute=_compute_is_user_assigned, search=_search_user_assigned)

    group = fields.Char(string="current assigned group", default=lambda self: self.GROUP_SUPPLIER)
    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(required=True, string="Name", size=50, copy=True)
    project_number = fields.Char(string="Project number (PSID)", required=True, copy=True);
    financial_code = fields.Char(string="Financial code", size=10, required=True, copy=True)
    shortname = fields.Char(string="Short name", required=True, copy=True)
    start_date = fields.Date(string="Start date", default=datetime.date.today(), copy=False);
    end_date = fields.Date(string="End date", copy=False);
    note = fields.Text(string="Note", track_visibility='onchange', copy=False)
    workflow_reason = fields.Text(string='Workflow reason', copy=False,
                                  help='Enter workflow reason mainly for actions "Return for repair" and "Cancel"')
    total_price = fields.Float(compute=_compute_amount_all, string='Total price', store=True, digits=(10, 2),
                               track_visibility='onchange', copy=False)
    vendor_id = fields.Many2one('res.partner', required=True, string='Vendor', track_visibility='onchange',
                                domain=partners_in_group_supplier, default=lambda self: self._get_default_vendor(), copy=True)
    pc_id = fields.Many2one('res.partner', string='PC', track_visibility='onchange', domain=partners_in_group_pc,
                            copy=True, default=lambda self: self._get_default_pc())
    pm_id = fields.Many2one('res.partner', string='PM', track_visibility='onchange', domain=partners_in_group_pm,
                            copy=True)
    manager_ids = fields.Many2many('res.partner', relation="o2net_quotation_manager_rel", string='Manager',
                                   domain=partners_in_group_manager, copy=False)
    assigned_persons_ids = fields.Many2many('res.partner', relation="o2net_quotation_assigned_rel",
                                            string='Assigned persons', copy=False,
                                            default=lambda self: self._get_default_assigned())

    state = fields.Selection(State, string='State', readonly=True, default='draft', track_visibility='onchange',
                             copy=False)
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

    duplicate_quots = fields.Integer(string="Duplicities", compute=_compute_duplicate_quots, compute_sudo=True, copy=False, store=False)

    @api.multi
    def write(self, vals):
        self.ensure_one()
        _logger.debug("quotation write")
        _logger.debug("vals: " + str(vals))

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

            self.message_post(body="<ul class =""o_mail_thread_message_tracking"">%s</ul>" % msg,
                              message_type="notification")

        res = super(Quotation, self).write(vals)

        # if STATE is written we came here from Workflow action and therefor we finish here. Automatic STATE change is only case of action 'SAVE'
        if not vals.get('state') == None:
            return res

        # change to 'IN_PROGRESS' if logged user is assigned to Quot and this is in state 'ASSIGNED'
        if self.vendor_id.id in self.assigned_persons_ids.ids:
            _logger.debug("CP je priradena dodavatelovy")
            if self.state == self.ASSIGNED:
                _logger.debug("CP je v stave ASSIGNED > stav sa automaticky meni na IN_PROGRESS")
                self.signal_workflow('in_progress')

        return res

    @api.multi
    def copy(self, default=None):

        # Qout name has to be unique, therefore add prefix [KOPIA]
        default = {'name': self.name + " [KOPIA]"}
        _logger.debug("copy (duplicate): " + str(default))
        new_cp = super(Quotation, self).copy(default=default)

        return new_cp

    @api.multi
    def unlink(self):
        if not self.state == self.DRAFT:
            raise AccessError(_("Only quotation in state 'DRAFT' can be unlink. In any other case use workflow action 'CANCEL'"))

    @api.onchange('vendor_id')
    def _find_pricelist(self):
        result = {}
        if not self.vendor_id:
            return result

        cennik_ids = self.env['o2net.pricelist'].search([('vendor_id', '=', self.vendor_id.id),
                                                         ('valid_from', '<=', datetime.date.today()),
                                                         ('valid_to', '>', datetime.date.today())], limit=1)

        if cennik_ids:
            self.price_list_id = cennik_ids[0]

        # by Vendor' change delete all pricelist's items
        self.quotation_item_ids = None;
        self.quotation_item_atyp_ids = None;
        self.quotation_item_package_ids = None;

        result = {'price_list_id': self.price_list_id}
        self.write(result)
        return result

    @api.onchange('state')
    def _set_state_date(self):
        self.state_date = datetime.date.today()

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError(_("Quotation with the same name already exists. Please enter an unique name."))

    # Workflow
    # looking for manager which 'total_price_limit' is greater than current quot total price
    def _find_managers(self):
        _logger.debug("Looking for manager to approve order of price " + str(self.total_price))
        partner_ids = self._partners_in_group(self.GROUP_MANAGER)
        manager_ids = self.env['res.partner'].search(
            [('id', 'in', partner_ids), ('po_total_price_limit', '<=', self.total_price)],
            order="po_total_price_limit desc")

        for man in manager_ids:
            _logger.debug(man.name)

        return manager_ids

    @api.multi
    def wf_draft(self):  # should be create but is set in field definition
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
            self.message_post(
                body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: %s </li></ul>" % self.workflow_reason,message_type="notification")


        self.send_mail([self.vendor_id])
        self.write({'workflow_reason': '', 'group': self.GROUP_SUPPLIER, 'state': self.ASSIGNED, 'assigned_persons_ids': [(6, 0, [self.vendor_id.id])]})
        return True

    @api.one
    def wf_in_progress(self):
        _logger.debug("workflow action to IN_PROGRESS")
        self.ensure_one()
        if self.workflow_reason:
            self.message_post(body="<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: " + self.workflow_reason + "</li></ul>")

        self.send_mail([self.pc_id], template_name='mail_cp_in_progress')
        self.write({'state': self.IN_PROGRESS,
                    'workflow_reason': '',
                    'group': self.GROUP_SUPPLIER,
                    'assigned_persons_ids': [(6, 0, [self.vendor_id.id])]})

        return True


    @api.multi
    def wf_confirm_to_approve(self):
        self.ensure_one()
        _logger.debug("workflow action wf_confirm_to_approve")

        wizard_view = self.env.ref('o2net.view_wizard_wf_confirm')
        _logger.debug('o2net.view_wizard_wf_confirm:' + str(wizard_view.id))

        return {
            "type": "ir.actions.act_window",
            "name": "Confirm quotation approval",
            "res_model": "o2net.wf_confirm",
            "views": [[wizard_view.id, "form"]],
            "context": {"signal": self.TO_APPROVE, "id": self.id},
            "target": "new"
        }

    @api.multi
    def wf_confirm_approve(self):
        self.ensure_one()
        _logger.debug("workflow action wf_confirm_approve")

        wizard_view = self.env.ref('o2net.view_wizard_wf_confirm')
        _logger.debug('o2net.view_wizard_wf_confirm:' + str(wizard_view.id))

        return {
            "type": "ir.actions.act_window",
            "name": "Confirm quotation approval",
            "res_model": "o2net.wf_confirm",
            "views": [[wizard_view.id, "form"]],
            "context": {"signal": self.APPROVE, "id": self.id},
            "target": "new"
        }

    @api.multi
    def wf_approve(self):
        self.ensure_one()
        _logger.debug("workflow action to APPROVE")

        # put 'workflow_reason' to history (mail_thread)
        if self.workflow_reason:
            # add to tracking values
            self.message_post(body=_("<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: %s </li></ul>") % self.workflow_reason,message_type="notification")

        # Vendor sent quot to be approved by PC
        if self.group == self.GROUP_SUPPLIER:
            _logger.debug("Supplier sent to approve by PC")
            self.send_mail([self.pc_id])
            self.write(
                {'state': self.TO_APPROVE,
                 'group': self.GROUP_PC,
                 'workflow_reason': ''})
            self.write({'assigned_persons_ids': [(6, 0, [self.pc_id.id])]})

        # PC sent quot to be approved by PM
        elif self.group == self.GROUP_PC:
            _logger.debug("PC sent to approve by PM")
            self.message_post(
                body=_("<ul class=""o_mail_thread_message_tracking""><li>: %s approved.</li></ul>") % self.pc_id.display_name.encode('ascii', 'ignore'),
                message_type="notification")
            self.send_mail([self.pm_id])
            self.write(
                {'state': self.TO_APPROVE,
                 'group': self.GROUP_PM,
                 'workflow_reason': '',
                 'assigned_persons_ids': [(6, 0, [self.pm_id.id])]})

        # PM sent quot to be approved by Manager
        elif self.group == self.GROUP_PM:
            _logger.debug("PM sent to approve by Manager")
            self.message_post(
                body=_("<ul class=""o_mail_thread_message_tracking""><li>: %s approved.</li></ul>") % self.pm_id.display_name.encode('ascii', 'ignore'),
                message_type="notification")
            manager_ids = self._find_managers()
            if manager_ids:
                self.send_mail(manager_ids)
                self.write(
                    {'state': self.TO_APPROVE,
                     'manager_ids': [(6, 0, manager_ids.ids)],
                     'group': self.GROUP_MANAGER,
                     'workflow_reason': '',
                     'assigned_persons_ids': [(6, 0, manager_ids.ids)]})
            else:
                _logger.debug("no managers found")
                raise UserError('No manager(s) found to assign.')

        # Manager approved
        elif self.group == self.GROUP_MANAGER:
            _logger.debug("Manager approved")
            manager = self.env.user.partner_id
            if not self.is_user_assigned:
                if len(self.assigned_persons_ids.ids) == 1:
                    manager = self.assigned_persons_ids[0]

            _logger.debug("Manager is '" + manager.display_name.encode('ascii', 'ignore'))
            self.message_post(
                body=_("<ul class=""o_mail_thread_message_tracking""><li>: %s approved.</li></ul>") % manager.display_name.encode('ascii', 'ignore'),
                message_type="notification")
            # send email to PC to let him know that quotation has been approved by manager
            context = {'manager_name': manager.display_name}
            self.send_mail([self.pc_id], template_name='mail_cp_manager_approved', context=context)
            self.write(
                {'workflow_reason': '',
                 'assigned_persons_ids': [(3, manager.id)]})

        return True

    def wf_all_managers_approved(self):
        _logger.debug("check if all managers approved")

        if self.group == self.GROUP_MANAGER:
            return not self.assigned_persons_ids.ids

        return False

    def wf_approved(self):
        _logger.debug("all managers approved")

        self.sudo().write(
            {'state': self.APPROVED,
             'group': '',
             'workflow_reason': '',
             'assigned_persons_ids': [(6, 0, [self.pc_id.id])]})

        self.action_exportSAP()
        self.send_mail([self.vendor_id, self.pc_id], template_name='mail_cp_approved')

        # send mail to SAP import person. use exported TXT file as attachement
        Attachment = self.env['ir.attachment']
        attachment_data = {
            'name': self.sap_export_file_name.encode('ascii', 'ignore'),
            'datas_fname': self.sap_export_file_name.encode('ascii', 'ignore'),
            'datas': self.sap_export_file_binary,
            'res_model': 'o2net.quotation',
            'res_id': self.id,
        }

        attachment_ids = []
        attachment_ids.append(Attachment.create(attachment_data).id)


        templateObj = self.get_mail_template("mail_cp_approved_sap_export")
        templateObj.attachment_ids = [(6, 0, attachment_ids)]
        mail_id = templateObj.send_mail(self.id, force_send=True, raise_exception=False)

        return mail_id

    @api.one
    def wf_not_complete(self):
        _logger.debug("workflow action to NOT_COMPLETE")
        self.ensure_one()

        self.wf_can_user_workflow()

        if self.workflow_reason:
            self.message_post(
                body=_("<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: %s </li></ul>") % self.workflow_reason.encode('ascii', 'ignore'))

        # PC signals 'not complete' - CP should be 'in_progress' and assigned to Supplier
        if self.pc_id.id in self.assigned_persons_ids.ids:
            _logger.debug("workflow action to IN_PROGRESS")
            self.send_mail([self.vendor_id])
            self.signal_workflow('not_complete')
            # code flow continues in method self.wf_in_progress()

        # PM signals 'not complete' - CP should be 'to_approve' and assigned to PC
        elif self.pm_id.id in self.assigned_persons_ids.ids:
            _logger.debug("workflow action to TO_APPROVE")
            self.send_mail([self.pc_id])
            self.write({'state': self.TO_APPROVE,
                        'workflow_reason': '',
                        'group': self.GROUP_PC,
                        'assigned_persons_ids': [(6, 0, [self.pc_id.id])]})

        return True

    @api.one
    def wf_cancel(self):
        _logger.debug("workflow action to CANCEL")
        self.ensure_one()

        if self.workflow_reason:
            self.message_post(
                body=_("<ul class =""o_mail_thread_message_tracking""><li>Workflow reason: %s </li></ul>") % self.workflow_reason.encode('ascii', 'ignore'))

        self.send_mail([self.vendor_id, self.pc_id], template_name='mail_cp_canceled')
        self.write({'state': self.CANCEL, 'workflow_reason': '', 'group': '', 'assigned_persons_ids': [(5, 0, 0)]})
        return True

    @api.one
    def wf_archive(self):
        _logger.debug("workflow action to ARCHIVE")
        self.message_post(
            body=_("<ul class=""o_mail_thread_message_tracking""><li>: %s archived quotation.</li></ul>") % self.env.user.partner_id.display_name.encode('ascii', 'ignore'),
            message_type="notification")
        self.write({'workflow_reason': '',
                    'active' : 0,
                    'assigned_persons_ids': [(5, 0, 0)]})
        return True

    @api.one
    def send_mail(self, partner_ids=None, template_name='mail_cp_assigned', context=None):
        _logger.debug("send mail to " + str(partner_ids))

        # Find the e-mail template (defined in views/mail_template.xml)
        templateObj = self.get_mail_template(template_name)

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

        return mail_id


    def get_mail_template(self, template_name='mail_cp_assigned'):
        _logger.debug("get mail template " + str(template_name))

        # Find the e-mail template (defined in views/mail_template.xml)
        template = self.env.ref('o2net.' + template_name)
        if not template:
            _logger.debug("unable get mail template: " + str(template_name))
            return

        templateObj = self.env['mail.template'].browse(template.id)

        admin = self.env['res.users'].browse(SUPERUSER_ID)
        if admin:
            _logger.debug("admin mail: " + admin.partner_id.email)
            templateObj.email_from = admin.partner_id.email

        templateObj.lang = self.env.user.partner_id.lang

        return templateObj
