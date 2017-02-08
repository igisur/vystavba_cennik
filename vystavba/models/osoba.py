# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Osoba(models.Model):
     _name = 'res.partner'
     _inherit = "res.partner"

     def _get_partner_sup(self):
          obj = self.pool.get('res.partner')
          ids = obj.search([('supplier', '=', True), ('is_company', '=', True)])
          res = obj.browse(ids)
          res = [(r['id'], r['name']) for r in res]
          return res

     kod = fields.Char(string="Kod", size=10)
     group_id = fields.Many2one('res.groups', string='Skupina', required=True,  selection=_get_partner_sup)
     cp_celkova_cena_limit = fields.Float(digits=(6,0), string="Celková cena cenovej ponuky", help="Za schvalenie objednavky pri prekroceni celkovej hodnoty je zodpovedna tato osoba.");
