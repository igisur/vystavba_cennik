# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class VystavbaCenovaPonukaPolozka(models.Model):
    _name = 'o2net.cenova_ponuka.polozka'
    _description = "o2net - price offer item"

    @api.depends('cena_jednotkova', 'mnozstvo')
    def _compute_cena_celkom(self):
        _logger.info("_compute_cena_celkom: " + str(len(self)))
        for line in self:
            if line.mnozstvo:
                line.cena_celkom = line.cena_jednotkova * line.mnozstvo

    @api.depends('cennik_polozka_id')
    def _compute_cena_jednotkova(self):
        _logger.info("_compute_cena_jednotkova: " + str(len(self)))
        for line in self:
            line.cena_jednotkova = line.cennik_polozka_id.cena

    cena_jednotkova = fields.Float(compute=_compute_cena_jednotkova, string='Unit price', store=True, digits=(10, 2))
    cena_celkom = fields.Float(compute=_compute_cena_celkom, string='Total price', store=True, digits=(10,2))
    mnozstvo = fields.Float(string='Quantity', digits=(5,2), required=True)
    cenova_ponuka_id = fields.Many2one('o2net.cenova_ponuka', string='Price offer', required=True, ondelete='cascade')
    cennik_polozka_id = fields.Many2one('o2net.cennik.polozka', string='Price list item', required=True, domain="[('cennik_id', '=', parent.cennik_id)]")
    polozka_mj = fields.Selection(related='cennik_polozka_id.mj', string='Measure unit', stored=False)
    polozka_popis = fields.Text(related='cennik_polozka_id.popis', string='Description', stored=False)
    polozka_isbalicek = fields.Boolean(related='cennik_polozka_id.is_balicek', string='Package', stored=True)
    name = fields.Char(related='cennik_polozka_id.name', string='Name')
    kod = fields.Char(related='cennik_polozka_id.kod', string='Code')
    currency_id = fields.Many2one(related='cenova_ponuka_id.currency_id', string="Currency")

