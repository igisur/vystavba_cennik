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
    'css': ['static/src/css/o2net.css'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        "sequences/site_sequence.xml",
        'views/views.xml',
        'views/resources.xml',
        'views/mail_template.xml',
        'views/partner_view.xml',
        'views/quot/quotation_view.xml',
        'views/quot/pricelist_view.xml',
        'views/quot/product_view.xml',
        'views/quot/section_view.xml',
        'views/quot/wizards_view.xml',
        'views/site/site_view.xml',
        'views/site/technology_view.xml',
        'workflows/quotation_wf.xml',
        'workflows/technology_wf.xml',
        'report/quotation_report.xml',
        'cron/quotation_cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}