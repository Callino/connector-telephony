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

from openerp import models, fields, api

class crm_phonecall(models.Model):
     _inherit = 'crm.phonecall'

     uniqueid = fields.Char(size=64, string="UniqueID")
     issue_id = fields.Many2one('project.issue', String="Issue")

class project_issue(models.Model):
     _inherit = 'project.issue'

     calls = fields.One2many('crm.phonecall', 'issue_id', string="UniqueID")