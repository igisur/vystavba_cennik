# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class VystavbaCenovaPonukaPolozka(models.Model):
    _name = 'o2net.cenova_ponuka.polozka'
    _description = "o2net - price offer item"

    @api.depends('unit_price', 'quantity')
    def _compute_total_price(self):
        _logger.info("_compute_total_price: " + str(len(self)))
        for line in self:
            if line.quantity:
                line.total_price = line.unit_price * line.quantity

    @api.depends('pricelist_item_id')
    def _compute_unit_price(self):
        _logger.info("_compute_unit_price: " + str(len(self)))
        for line in self:
            line.unit_price = line.pricelist_item_id.price

    unit_price = fields.Float(compute=_compute_unit_price, string='Unit price', store=True, digits=(10, 2))
    total_price = fields.Float(compute=_compute_total_price, string='Total price', store=True, digits=(10,2))
    quantity = fields.Float(string='Quantity', digits=(5,2), required=True)
    price_offer_id = fields.Many2one('o2net.cenova_ponuka', string='Price offer', required=True, ondelete='cascade')
    pricelist_item_id = fields.Many2one('o2net.cennik.polozka', string='Price list item', required=True, domain="[('price_list_id', '=', parent.price_list_id)]")
    item_unit_of_measure = fields.Selection(related='pricelist_item_id.unit_of_measure', string='Measure unit', stored=False)
    item_description = fields.Text(related='pricelist_item_id.description', string='Description', stored=False)
    item_is_package = fields.Boolean(related='pricelist_item_id.is_package', string='Package', stored=True)
    name = fields.Char(related='pricelist_item_id.name', string='Name')
    code = fields.Char(related='pricelist_item_id.code', string='Code')
    currency_id = fields.Many2one(related='pricelist_item_id.currency_id', string="Currency")

