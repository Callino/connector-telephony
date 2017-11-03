# -*- encoding: utf-8 -*-
# -*- coding: utf-8 -*-
##############################################################################
#
#    Mirta PBX Connector module for Odoo
#    Copyright (C) 2017 Pichler Wolfgang <wpichler@callino.at>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http
from openerp import SUPERUSER_ID
import logging


_logger = logging.getLogger(__name__)


class ClidLookup(http.Controller):

    @http.route('/clid/lookup/<clid>', auth='public')
    def lookup(self, clid, **kw):
        _logger.debug("got %r", clid)
        phone_obj = http.request.registry.get('phone.common')
        entrie = phone_obj.get_record_from_phone_number(http.request.cr, SUPERUSER_ID, clid)
        if not entrie:
            return "Unbekannt"
        src_obj = http.request.registry.get(entrie[0])
        src_ins = src_obj.browse(http.request.cr, SUPERUSER_ID, entrie[1])
        if not src_ins:
            return "Unbekannt"
        return src_ins.display_name
