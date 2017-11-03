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
import json

_logger = logging.getLogger(__name__)

class RegisterCall(http.Controller):
    @http.route('/register_call/createCall', auth='public')
    def create_call(self, **kw):
        src = http.request.params.get('src')
        srcname = http.request.params.get('srcname')
        dst = http.request.params.get('dst')
        dstname = http.request.params.get('dstname')
        uniqueid = http.request.params.get('uniqueid')
        issue = http.request.params.get('issue')
        phonecall_obj = http.request.registry.get('crm.phonecall')
        phone_obj = http.request.registry.get('phone.common')
        user_obj = http.request.registry.get('res.users')
        user = phone_obj.get_record_from_phone_number(http.request.cr, SUPERUSER_ID, dst)
        user_ids = None
        if user and user[0] == 'res.partner':
            user_ids = user_obj.search(http.request.cr, SUPERUSER_ID, [('partner_id', '=', user[1])])
        partner = phone_obj.get_record_from_phone_number(http.request.cr, SUPERUSER_ID, src)
        if partner:
            src_obj = http.request.registry.get(partner[0])
            src_ins = src_obj.browse(http.request.cr, SUPERUSER_ID, partner[1])
        else:
            src_ins = None
        if not srcname:
            srcname = 'Unbekannt'
        if not dstname:
            dstname = 'Unbekannt'
        if issue and issue == 'new':
            issue_obj = http.request.registry.get('project.issue')
            issue = {
                'name': 'Neues Trouble Ticket durch Anruf',
                'user_id': (user_ids[0] if len(user_ids) == 1 else None),
                'partner_id': (partner[1] if partner and partner[0] == 'res.partner' else None),
            }
            issue_id = issue_obj.create(http.request.cr, SUPERUSER_ID, issue)
        call = {
            'name': srcname + '<' + src + '>' + ' zu ' + dstname + '<' + dst + '>',
            'state': 'open',
            'partner_id': (partner[1] if partner and partner[0] == 'res.partner' else None),
            'user_id': (user_ids[0] if len(user_ids) == 1 else None),
            'uniqueid': uniqueid,
            'issue_id': issue_id,
        }
        phonecall_obj.create(http.request.cr, SUPERUSER_ID, call)
        return src_ins.display_name if src_ins else src

    @http.route('/register_call/endCall', auth='public')
    def end_call(self, **kw):
        _logger.info("got http post %r", http.request.params)
        uniqueid = http.request.params.get('uniqueid')
        duration = http.request.params.get('duration')
        disposition = http.request.params.get('disposition')
        phonecall_obj = http.request.registry.get('crm.phonecall')
        phonecall_ids = phonecall_obj.search(http.request.cr, SUPERUSER_ID, [('uniqueid','=',uniqueid)])
        if not (len(phonecall_ids) == 1):
            _logger.error("got end request for call i do not know about...")
            return "Not Ok"
        call = {
            'state': ('done' if disposition == 'ANSWERED' else 'cancel'),
            'duration': float(duration) / 60 / 60,
        }
        phonecall_obj.write(http.request.cr, SUPERUSER_ID, phonecall_ids[0], call)
        return "Ok"
