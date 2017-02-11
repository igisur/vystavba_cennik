# -*- coding: utf-8 -*-
from openerp import http

class VystavbaExportSAP(http.Controller):
     @http.route('/vystavba/exportSAP/', auth='public', type='http')
     def index(self, **kw):
         return "Hello, world"

     @http.route('/vystavba/objects/', auth='public', type='http')
     def list(self, **kw):
         return http.request.render('vystavba.listing', {
             'root': '/vystavba/',
             'objects': http.request.env['vystavba.cenova_ponuka'].search([]),
         })

     @http.route('/vystavba/objects/<model("vystavba.cenova_ponuka"):obj>/', auth='public', type='http')
     def object(self, obj, **kw):
         return http.request.render('vystavba.object', {
             'object': obj
         })

