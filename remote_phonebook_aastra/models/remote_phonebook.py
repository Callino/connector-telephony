from openerp import models, fields, api
import logging
# import xml.etree.ElementTree as ET
from lxml import etree as ET
import urllib

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
    def _get_default_phone_list(self, partners):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % "test"
        root = self._get_AastraIPPhoneTextMenu_root(cancel_action=cancel_action)
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
    def _get_default_phone_list_customer(self, partners):
        return self._get_default_phone_list(partners)

    @api.model
    def _get_default_phone_list_supplier(self, partners):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % "test"
        root = self._get_AastraIPPhoneTextMenu_root(cancel_action=cancel_action)
        for partner in partners:
            entry = ET.SubElement(root, 'MenuItem')
            name = ET.SubElement(entry, 'Prompt')
            name.text = partner.name
            uri = ET.SubElement(entry, 'URI')
            uri.text = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/supplier?%s" % urllib.urlencode({'id': str(partner.id)})
        return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")

    @api.model
    def letter_screen(self, partner_dict, type):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % "test"
        root = self._get_AastraIPPhoneTextMenu_root(cancel_action=cancel_action)
        for letter, partners in partner_dict[0].iteritems():
            entry = ET.SubElement(root, 'MenuItem')
            name = ET.SubElement(entry, 'Prompt')
            name.text = letter
            uri = ET.SubElement(entry, 'URI')
            uri.text = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/partners?%s" % urllib.urlencode({'ids': str(partners)})
        return ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes")

    @api.model
    def get_content_aastra_supplier(self):
        partners = self._get_sellers()
        if len(partners) > 25:
            split_partners = self.split_partners(partners)
            return self.letter_screen(split_partners, "supplier")
        else:
            return self._get_default_phone_list_supplier(partners)

    @api.model
    def get_content_aastra_customers(self):
        partners = self._get_customers()
        if len(partners) > 25:
            split_partners = self.split_partners(partners)
            return self.letter_screen(split_partners, "customers")
        else:
            return self._get_default_phone_list_customer(partners)

    @api.model
    def get_content_aastra_all(self):
        partners = self._get_partners()
        if len(partners) > 25:
            split_partners = self.split_partners(partners)
            return self.letter_screen(split_partners, "all")
        else:
            return self._get_default_phone_list(partners)

    @api.model
    def get_content_for_supplier(self, partners):
        cancel_action = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/supplier/test"
        root = self._get_AastraIPPhoneTextMenu_root(cancel_action=cancel_action)
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
    def get_content_for_partners(self, partners):
        return self._get_default_phone_list(partners)

    @api.model
    def _get_AastraIPPhoneTextMenu_root(self, name="Telefonbuch", cancel_action=None):
        root = ET.Element('AastraIPPhoneTextMenu')
        if cancel_action:
            root.set('cancelAction', cancel_action)
        title = ET.SubElement(root, 'Title')
        title.text = name
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Neuer Eintrag"
        uri = ET.SubElement(new, 'URI')
        uri.text = self.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/new_entry/1" % type
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Suche"
        uri = ET.SubElement(new, 'URI')
        uri.text = self.env['ir.config_parameter'].get_param(
            'web.base.url') + "/aastra/phonebook/%s/search_screen" % type
        return root

    def _get_content(self):
        if self.type == 'aastra':
            _logger.info("do return content for type aastra")
            return self._get_content_aastra('all')
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
