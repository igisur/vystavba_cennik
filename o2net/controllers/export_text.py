# -*- coding: utf-8 -*-
from openerp import http

class export_text(http.Controller):
     @http.route('/o2net/exportSAP/', auth='public', type='http')
     def index(self, **kw):
         return "Hello, world"

     @http.route('/o2net/objects/', auth='public', type='http')
     def list(self, **kw):
         return http.request.render('vystavba.listing', {
             'root': '/o2net/',
             'objects': http.request.env['o2net.cenova_ponuka'].search([]),
         })

     @http.route('/o2net/objects/<model("o2net.cenova_ponuka"):obj>/', auth='public', type='http')
     def object(self, obj, **kw):
         return http.request.render('o2net.object', {
             'object': obj
         })

