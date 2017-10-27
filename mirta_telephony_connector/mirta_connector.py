# -*- encoding: utf-8 -*-
##############################################################################
#
#    OVH connector module for Odoo
#    Copyright (C) 2015 Alexis de Lattre <alexis@via.ecp.fr>
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
import urllib2

_logger = logging.getLogger(__name__)


class res_company(models.Model):
    _inherit = "res.company"

    mirta_url = fields.Char(string='Mirta Base URL')
    mirta_tenant = fields.Char(string='Mirta Tenant Code')
    mirta_key = fields.Char(string="Mirta API Key")


class ResUsers(models.Model):
    _inherit = "res.users"

    mirta_callerid = fields.Char(string='Mirta CallerID')
    mirta_extension = fields.Char(string="User Extension")


class PhoneCommon(models.AbstractModel):
    _inherit = 'phone.common'

    @api.model
    def click2dial(self, erp_number):
        res = super(PhoneCommon, self).click2dial(erp_number)
        if not erp_number:
            raise Warning(
                _('Missing phone number'))

        user = self.env.user
        if not user.mirta_callerid:
            raise Warning(
                _('Missing Mirta CallerID on user %s') % user.name)

        if not user.mirta_extension:
            raise Warning(
                _('Missing Mirta Extension Number on user %s') % user.name)

        if not user.company_id.mirta_key:
            raise Warning(
                _('Missing Company Mirta key on company %s') % user.company_id.name)

        if not user.company_id.mirta_tenant:
            raise Warning(
                _('Missing Mirta tenant code on company %s') % user.company_id.name)

        if not user.company_id.mirta_url:
            raise Warning(
                _('Missing Mirta Base URL on company %s') % user.company_id.name)

        called_number = self.convert_to_dial_number(erp_number)
        url = "%sproxyapi.php?reqtype=DIAL&tenant=%s&key=%s&source=%s&dest=%s&destclid=%s" % \
              (user.company_id.mirta_url,
               user.company_id.mirta_tenant,
               user.company_id.mirta_key,
               user.mirta_extension,
               called_number,
               user.mirta_callerid)
        result = urllib2.urlopen(url, None, 5)
        _logger.info("Click2dial URL: %s", url)
        _logger.info("Result: %r", result)

        res['dialed_number'] = called_number
        return res
