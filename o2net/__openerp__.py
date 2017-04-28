# -*- coding: utf-8 -*-
{
    'name': "O2 network",
    'summary': """Builders price list""",
    'description': """Builders price list enables you to track your vendors' quotations""",
    'author': "Igor Surovy / Branislav Vilmon",
    'website': "http://www.o2.sk",
    'category': 'o2net',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/cennik_view.xml',
        'views/polozka_view.xml',
        'views/osoba_view.xml',
        'views/cenova_ponuka_view.xml',
        'report/report.xml',
        'views/oddiel_view.xml',
        'views/mail_template.xml',
        'workflows/quotation_wf.xml',
        'report/report_cenova_ponuka.xml',
        'views/cenova_ponuka_cron.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}