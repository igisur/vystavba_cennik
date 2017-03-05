# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp import tools

class o2net_cenova_ponuka_report(osv.Model):
    _name = "o2net.cenova_ponuka_report"
    _description = "Cenova ponuka report"
    _auto = False
    _columns = {
        'typ': fields.char('Typ', size=2, readonly=True),
        'oddiel': fields.char('Oddiel', size=128, readonly=True),
        'polozka': fields.char('Oddiel', size=128, readonly=True),
        'cena_jednotkova': fields.float('Planned Amount', readonly=True),
        'mj': fields.char('Merná jednotka', size=100, readonly=True),
        'pocet': fields.float('Pocet', readonly=True),
        'cena_celkom': fields.float('Planned Amount', readonly=True),
        'cislo': fields.char('Cislo', readonly=True)
    }
    _order = 'typ asc, oddiel asc'

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'o2net_cenova_ponuka_report')
        cr.execute\
        ("""
            CREATE OR REPLACE VIEW o2net_cenova_ponuka_report AS
            (
                select typ, cp.id as id, oddiel, polozka, cena_jednotkova, mj, pocet, cena_celkom, cp.cislo as cislo
                    from
                    (
                    select '1t' as typ, cpp.cenova_ponuka_id as cp_id, o.name as oddiel, p.name as polozka, cpp.cena_jednotkova as cena_jednotkova, p.mj as mj, cpp.mnozstvo as pocet, cpp.cena_celkom as cena_celkom
                    from o2net_cenova_ponuka_polozka cpp
                    join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                    join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = false
                    join o2net_oddiel o on p.oddiel_id = o.id
                    -- where cpp.cenova_ponuka_id = %s
                    union all
                    select '2a',cppa.cenova_ponuka_id, o.name, cppa.name, null, null, null, cppa.cena
                    from o2net_cenova_ponuka_polozka_atyp cppa
                    join o2net_oddiel o on cppa.oddiel_id = o.id
                    -- where cppa.cenova_ponuka_id = %s
                    union all
                    select '3b',cpp.cenova_ponuka_id, o.name, p.name, cpp.cena_jednotkova, p.mj, cpp.mnozstvo, cpp.cena_celkom
                    from o2net_cenova_ponuka_polozka cpp
                    join o2net_cennik_polozka cp on cpp.cennik_polozka_id = cp.id
                    join o2net_polozka p on cp.polozka_id = p.id and p.is_balicek = true
                    join o2net_oddiel o on p.oddiel_id = o.id
                    -- where cpp.cenova_ponuka_id = %s

                    ) zdroj
                    join o2net_cenova_ponuka cp on zdroj.cp_id = cp.id
            )
        """)

o2net_cenova_ponuka_report()