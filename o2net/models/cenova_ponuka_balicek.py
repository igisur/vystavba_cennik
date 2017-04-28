# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VystavbaCenovaPonukaPolozkaBalicek(models.Model):
    _name = 'o2net.cenova_ponuka.polozka_balicek'
    _inherit = 'o2net.cenova_ponuka.polozka'
    _description = "o2net - price offer package"
