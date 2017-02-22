# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaPolozka(models.Model):
    _name = 'o2.vys.polozka'
    _description = "Vystavba - polozka cennika"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(required=True, string="Názov", size=100)
    kod = fields.Char(required=True, string="Kód", size=20)
    description = fields.Text(string="Popis", size=1000, default="")
    # Many2one display "name" field value or _rec_name = "field_name"
    # oddiel_id = fields.Many2One('vystavba.oddiel', required=True, string="Oddiel", help="kod oddielu pre SAP")
    # oddiel_id = fields.Char(size=10, required=True, string="Oddiel", help="kod oddielu pre SAP")
    oddiel_id = fields.Many2one('o2.vys.oddiel', string='Oddiel', required=True)
    mj = fields.Selection([
        ('_', 'neurčená MJ'),
        ('kg', 'Kilogram'),
        ('ks', 'Kus'),
        ('km', 'Kilometer'),
        ('hod', 'Hodina'),
        ('m', 'Meter'),
        ('m2', 'Meter kubicky'),
        ('m3', 'Meter stvorcovy'),
        ('sada', 'sada'),
        ('vl.', 'vl'),
    ], string="Merná jednotka", default="_")
    is_balicek = fields.Boolean("Balíček", default=False)

    intern_id = fields.Char(string="Intern ID")
    intern_kod = fields.Char(string="Intern kód")


    # vyhladavame iba podla mena polozky. kod sluzi pre SAP
    # @api.multi
    # @api.depends('name', 'kod')
    # def name_get(self):
    #     result = []
    #     for po in self:
    #         name = po.kod + " " + po.name
    #         result.append((po.id, name))
    #     return result

    # def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
    #     if context is None:
    #         context = {}
    #     if not args:
    #         args = []
    #     if name:
    #         positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
    #         ids = []
    #         if operator in positive_operators:
    #             ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
    #             if not ids:
    #                 ids = self.search(cr, user, [('barcode','=',name)]+ args, limit=limit, context=context)
    #         if not ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
    #             # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
    #             # on a database with thousands of matching products, due to the huge merge+unique needed for the
    #             # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
    #             # Performing a quick memory merge of ids in Python will give much better performance
    #             ids = self.search(cr, user, args + [('default_code', operator, name)], limit=limit, context=context)
    #             if not limit or len(ids) < limit:
    #                 # we may underrun the limit because of dupes in the results, that's fine
    #                 limit2 = (limit - len(ids)) if limit else False
    #                 ids += self.search(cr, user, args + [('name', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
    #         elif not ids and operator in expression.NEGATIVE_TERM_OPERATORS:
    #             ids = self.search(cr, user, args + ['&', ('default_code', operator, name), ('name', operator, name)], limit=limit, context=context)
    #         if not ids and operator in positive_operators:
    #             ptrn = re.compile('(\[(.*?)\])')
    #             res = ptrn.search(name)
    #             if res:
    #                 ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
    #         # still no results, partner in context: search on supplier info as last hope to find something
    #         if not ids and context.get('partner_id'):
    #             supplier_ids = self.pool['product.supplierinfo'].search(
    #                 cr, user, [
    #                     ('name', '=', context.get('partner_id')),
    #                     '|',
    #                     ('product_code', operator, name),
    #                     ('product_name', operator, name)
    #                 ], context=context)
    #             if supplier_ids:
    #                 ids = self.search(cr, user, [('product_tmpl_id.seller_ids', 'in', supplier_ids)], limit=limit, context=context)
    #     else:
    #         ids = self.search(cr, user, args, limit=limit, context=context)
    #     result = self.name_get(cr, user, ids, context=context)
    #     return result

