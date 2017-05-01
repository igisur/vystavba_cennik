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
        'views/pricelist_view.xml',
        'views/product_view.xml',
        'views/partner_view.xml',
        'views/priceoffer_view.xml',
        'report/report.xml',
        'views/section_view.xml',
        #'views/email_template.xml'
        'workflows/priceoffer_wf.xml',
        'report/priceoffer_report.xml',
        'views/priceoffer_cron.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}