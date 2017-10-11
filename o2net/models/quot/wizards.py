# -*- coding: utf-8 -*-

import base64
import datetime
import logging

from openerp import models, fields, api

_logger = logging.getLogger(__name__)

class WfConfirm(models.TransientModel):
    _name = 'o2net.wf_confirm'

    @api.multi
    def confirm(self):
        _logger.debug("confirm")
        _logger.debug("_context:" + str(self._context))

        ids = [self._context['id']]
        records = self.env['o2net.quotation'].browse(ids)

        signal = self._context['signal']
        records.signal_workflow(signal)

        return {}
