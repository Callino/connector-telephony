from openerp import models, fields, api
import logging
# import xml.etree.ElementTree as ET
from lxml import etree as ET
import urllib
import collections

_logger = logging.getLogger(__name__)


class remote_phonebook(models.Model):
    _inherit = 'remote.phonebook'

    def _get_sellers(self):
        return self.env['res.partner'].search([('supplier', '=', True), ('parent_id', '=', False)])

    def _get_customers(self):
        return self.env['res.partner'].search([('customer', '=', True)])

    def _get_partners(self):
        if self.type == 'aastra':
            return self.env['res.partner'].search([])
        return super(remote_phonebook, self)._get_partners()

    def _get_type(self):
        types = super(remote_phonebook, self)._get_type()
        types.append(('aastra', 'Aastra'))
        return types

    def _get_content_aastra(self, type):
        if type == 'supplier':
            return self.get_content_aastra_supplier()
        elif type == 'customers':
            return self.get_content_aastra_customers()
        elif type == 'all':
            return self.get_content_aastra_all()
        else:
            raise ValueError("Unknown Type: %r" % type)

    @api.model
    def _get_default_phone_list(self, partners, tokken, type="all"):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % tokken
        root = self._get_AastraIPPhoneTextMenu_root(tokken, type, cancel_action=cancel_action)
        # create simple entries to call contacts
        for partner in partners:
            if partner.phone:
                entry = ET.SubElement(root, 'MenuItem')
                name = ET.SubElement(entry, 'Prompt')
                name.text = partner.name
                uri = ET.SubElement(entry, 'URI')
                uri.text = "Dial: %s" % partner.phone
                dial = ET.SubElement(entry, 'Dial')
                dial.text = partner.phone
            if partner.mobile:
                entry = ET.SubElement(root, 'MenuItem')
                name = ET.SubElement(entry, 'Prompt')
                name.text = partner.name
                uri = ET.SubElement(entry, 'URI')
                uri.text = "Dial: %s" % partner.mobile
                dial = ET.SubElement(entry, 'Dial')
                dial.text = partner.mobile
        return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")

    @api.model
    def _get_default_phone_list_customer(self, partners, tokken):
        return self._get_default_phone_list(partners, tokken, type="customer")

    @api.model
    def _get_default_phone_list_supplier(self, partners, tokken):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % tokken
        root = self._get_AastraIPPhoneTextMenu_root(tokken, "supplier", cancel_action=cancel_action)
        for partner in partners:
            entry = ET.SubElement(root, 'MenuItem')
            name = ET.SubElement(entry, 'Prompt')
            name.text = partner.name
            uri = ET.SubElement(entry, 'URI')
            uri.text = self.env['ir.config_parameter'].get_param(
                'web.base.url') + "/aastra/phonebook/%s/suppliers?%s" % (tokken, urllib.urlencode({'ids': str(partner.id)}))
        return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")

    @api.model
    def letter_screen(self, partner_dict, type, tokken):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % tokken
        root = self._get_AastraIPPhoneTextMenu_root(tokken, type, cancel_action=cancel_action)
        for letter, partners in collections.OrderedDict(sorted(partner_dict.items(), key=lambda t: t[0])).iteritems():
            entry = ET.SubElement(root, 'MenuItem')
            name = ET.SubElement(entry, 'Prompt')
            name.text = "%s - %i Kontakte" % (letter, partners[0])
            uri = ET.SubElement(entry, 'URI')
            if type == 'supplier':
                uri.text = self.env['ir.config_parameter'].get_param(
                    'web.base.url') + "/aastra/phonebook/%s/partners/%s/%s" % (tokken, type, letter)
            else:
                uri.text = self.env['ir.config_parameter'].get_param(
                    'web.base.url') + "/aastra/phonebook/%s/partners/%s/%s" % (tokken, type, letter)
        return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")

    @api.model
    def get_content_aastra_supplier(self):
        count_sql = "select count(*) from res_partner as p1 where active and parent_id is null and supplier and not customer and (phone is not null or mobile is not null or (SELECT count(*) from res_partner WHERE parent_id=p1.id AND (phone is not null or mobile is not null) )>0)"
        split_sql = "select substring(upper(name) from 1 for 1), count(*) from res_partner as p1 where active and parent_id is null and supplier and (phone is not null or mobile is not null or (SELECT count(*) from res_partner WHERE parent_id=p1.id AND (phone is not null or mobile is not null) )>0) group by substring(upper(name) from 1 for 1) order by substring(upper(name) from 1 for 1);"
        self._cr.execute(count_sql)
        count_result = self._cr.fetchall()[0]
        if count_result > 25:
            split_partners = {}
            self._cr.execute(split_sql)
            split_result = self._cr.fetchall()
            for line in split_result:
                split_partners[line[0]] = []
            for line in split_result:
                split_partners[line[0]].append(line[1])
            return self.letter_screen(split_partners, "supplier", self.tokken)
        else:
            partners = self._get_sellers()
            return self._get_default_phone_list_supplier(partners)

    @api.model
    def get_content_aastra_customers(self):
        count_sql = "select count(*) from res_partner as p1 where active and parent_id is null and customer and not supplier and (phone is not null or mobile is not null or (SELECT count(*) from res_partner WHERE parent_id=p1.id AND (phone is not null or mobile is not null) )>0)"
        split_sql = "select substring(upper(name) from 1 for 1), count(id) from res_partner as p1 where active and parent_id is null and customer and (phone is not null or mobile is not null or (SELECT count(*) from res_partner WHERE parent_id=p1.id AND (phone is not null or mobile is not null) )>0) group by substring(upper(name) from 1 for 1) order by substring(upper(name) from 1 for 1);"
        self._cr.execute(count_sql)
        count_result = self._cr.fetchall()[0]
        if count_result > 25:
            split_partners = {}
            self._cr.execute(split_sql)
            split_result = self._cr.fetchall()
            for line in split_result:
                split_partners[line[0]] = []
            for line in split_result:
                split_partners[line[0]].append(line[1])
            return self.letter_screen(split_partners, "customers", self.tokken)
        else:
            partners = self._get_customers()
            return self._get_default_phone_list_customer(partners)

    @api.model
    def get_content_aastra_all(self):
        count_sql = "select count(*) from res_partner as p1 where active and parent_id is null and (phone is not null or mobile is not null or (SELECT count(*) from res_partner WHERE parent_id=p1.id AND (phone is not null or mobile is not null) )>0)"
        split_sql = "select substring(upper(name) from 1 for 1), count(*) from res_partner as p1 where active and parent_id is null and (phone is not null or mobile is not null or (SELECT count(*) from res_partner WHERE parent_id=p1.id AND (phone is not null or mobile is not null) )>0) group by substring(upper(name) from 1 for 1) order by substring(upper(name) from 1 for 1);"
        self._cr.execute(count_sql)
        count_result = self._cr.fetchall()[0]
        if count_result > 25:
            split_partners = {}
            self._cr.execute(split_sql)
            split_result = self._cr.fetchall()
            for line in split_result:
                split_partners[line[0]] = []
            for line in split_result:
                split_partners[line[0]].append(line[1])
            return self.letter_screen(split_partners, "all", self.tokken)
        else:
            partners = self._get_partners()
            return self._get_default_phone_list(partners)

    @api.model
    def get_content_for_supplier(self, partners, tokken):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/supplier" % tokken
        root = self._get_AastraIPPhoneTextMenu_root(tokken, "supplier", cancel_action=cancel_action)
        for partner in partners:
            if partner.phone:
                entry = ET.SubElement(root, 'MenuItem')
                name = ET.SubElement(entry, 'Prompt')
                name.text = "%s - Telefon" % partner.name
                uri = ET.SubElement(entry, 'URI')
                uri.text = "Dial: %s" % partner.phone
                dial = ET.SubElement(entry, 'Dial')
                dial.text = partner.phone
            if partner.mobile:
                entry = ET.SubElement(root, 'MenuItem')
                name = ET.SubElement(entry, 'Prompt')
                name.text = "%s - Mobil" % partner.name
                uri = ET.SubElement(entry, 'URI')
                uri.text = "Dial: %s" % partner.mobile
                dial = ET.SubElement(entry, 'Dial')
                dial.text = partner.mobile
            if partner.is_company:
                for sub_partner in partner.child_ids:
                    if sub_partner.phone:
                        entry = ET.SubElement(root, 'MenuItem')
                        name = ET.SubElement(entry, 'Prompt')
                        name.text = "%s - Telefon" % sub_partner.name
                        uri = ET.SubElement(entry, 'URI')
                        uri.text = "Dial: %s" % sub_partner.phone
                        dial = ET.SubElement(entry, 'Dial')
                        dial.text = sub_partner.phone
                    if sub_partner.mobile:
                        entry = ET.SubElement(root, 'MenuItem')
                        name = ET.SubElement(entry, 'Prompt')
                        name.text = "%s - Mobil" % sub_partner.name
                        uri = ET.SubElement(entry, 'URI')
                        uri.text = "Dial: %s" % sub_partner.mobile
                        dial = ET.SubElement(entry, 'Dial')
                        dial.text = sub_partner.mobile
        return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")

    @api.model
    def get_content_for_partners(self, partners, tokken):
        return self._get_default_phone_list(partners, tokken)

    @api.model
    def _get_AastraIPPhoneTextMenu_root(self, tokken, type, name="Telefonbuch", cancel_action=None):
        root = ET.Element('AastraIPPhoneTextMenu')
        if cancel_action:
            root.set('cancelAction', cancel_action)
        title = ET.SubElement(root, 'Title')
        title.text = name
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Neuer Eintrag"
        uri = ET.SubElement(new, 'URI')
        uri.text = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/%s/new_entry/1" % (tokken, type)
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Suche"
        uri = ET.SubElement(new, 'URI')
        uri.text = self.env['ir.config_parameter'].get_param(
            'web.base.url') + "/aastra/phonebook/%s/%s/search_screen" % (tokken, type)
        return root

    def _get_content(self):
        if self.type == 'aastra':
            _logger.info("do return content for type aastra")
            # return self._get_content_aastra('all')
        return super(remote_phonebook, self)._get_content()

    def _get_url(self):
        if self.type == 'aastra':
            _logger.info("do return url for type aastra")
            self.url = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/" + self.tokken
        else:
            return super(remote_phonebook, self)._get_url()

    type = fields.Selection(selection=_get_type)
    content = fields.Char('Phonebook content', compute=_get_content)
    url = fields.Char('Access URL', compute=_get_url)

    @api.one
    def split_partners(self, partners):
        _logger.info("Length partners: %r", partners)
        letter_dict = {}
        for partner in partners:
            if not partner.name[0].upper() in letter_dict:
                letter_dict[partner.name[0].upper()] = []
            letter_dict[partner.name[0].upper()].append(partner.id)
        _logger.info("Split into letters: %r", letter_dict)
        return letter_dict
