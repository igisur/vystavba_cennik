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
        'views/views.xml',
        'views/pricelist_view.xml',
        'views/product_view.xml',
        'views/partner_view.xml',
        'views/wizards_view.xml',
        'views/quotation_view.xml',
        'views/section_view.xml',
        'views/mail_template.xml',
        'workflows/quotation_wf.xml',
        'report/quotation_report.xml',
        'views/quotation_cron.xml',
        'views/resources.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}