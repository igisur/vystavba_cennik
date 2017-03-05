# -*- coding: utf-8 -*-

import time
from openerp import api, models
import logging

_logger = logging.getLogger(__name__)


class ReportCenovaPonuka(models.AbstractModel):
    _name = 'report.o2net.report_cenova_ponuka_pdf'

    @api.one
    def _get_rows(self, cp_id):
        data = []
        _logger.info("a_function_name")
        _logger.info("_get_rows: " + str(cp_id))

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

    @api.multi
    def render_html(self, data):

        _logger.info("RENDER HTML")
        _logger.info("self: " + str(self.id))
        _logger.info("data: " + str(data))

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('o2net.report_cenova_ponuka_pdf')
        docargs = {
            'doc_ids': [self.id],
            'doc_model': report.model,
            'data': data,
            'docs': self.env['o2net.cenova_ponuka'].browse(self.id),
            'get_rows': self._get_rows,
        }

        return report_obj.render('o2net.report_cenova_ponuka_pdf', docargs)
