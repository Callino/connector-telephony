# -*- coding: utf-8 -*-
from openerp import http
import logging
from lxml import etree as ET
from werkzeug.utils import redirect
import urllib

_logger = logging.getLogger(__name__)


class AastraPhonebook(http.Controller):

    @http.route('/aastra/phonebook/<tokken>', auth='public')
    def preselect(self, **kw):
        _logger.debug("got %r", kw)
        if 'tokken' not in kw:
            return "Invalid tokken"
        root = ET.Element('AastraIPPhoneTextMenu')
        # cancel_action = ""
        # root.set('cancelAction', cancel_action)
        # root.set('wrap', 'no')
        title = ET.SubElement(root, 'Title')
        title.text = "Hauptmenu"
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Lieferanten"
        uri = ET.SubElement(new, 'URI')
        uri.text = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/supplier/%s" % kw['tokken']
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Kunden"
        uri = ET.SubElement(new, 'URI')
        uri.text = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/customers/%s" % kw['tokken']
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Alle"
        uri = ET.SubElement(new, 'URI')
        uri.text = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/all/%s" % kw['tokken']

        response = http.request.make_response(ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes"),
                                              headers=[('Content-Type', 'text/xml')])
        return response

    @http.route('/aastra/phonebook/partners/<type>', auth='public')
    def get_phonebook_by_ids(self, **kw):
        if 'ids' not in kw:
            return "Invalid IDs"
        if 'type' not in kw:
            return "Invalid Type"
        else:
            partner_list = urllib.unquote(kw['ids'].strip('[],').replace(",", "")).decode('utf8').split()
            cleaned_partner_list = map(int, partner_list)
            partners = http.request.env['res.partner'].sudo().browse(cleaned_partner_list)
            if kw['type'] == 'supplier':
                content = http.request.env['remote.phonebook'].get_content_for_partners(partners)
            else:
                content = http.request.env['remote.phonebook'].get_content_for_supplier(partners)
            response = http.request.make_response(
                content,
                headers=[('Content-Type', 'text/xml')])
            return response

    @http.route('/aastra/phonebook/supplier', auth='public')
    def get_supplier_by_id(self, **kw):
        if 'id' not in kw:
            return "Invalid ID"
        else:
            partner_list = urllib.unquote(kw['id'].strip('[],').replace(",", "")).decode('utf8').split()
            cleaned_partner_list = map(int, partner_list)
            partners = http.request.env['res.partner'].sudo().browse(cleaned_partner_list)
            content = http.request.env['remote.phonebook'].get_content_for_supplier(partners)
            response = http.request.make_response(
                content,
                headers=[('Content-Type', 'text/xml')])
            return response

    @http.route('/aastra/phonebook/<type>/<tokken>', auth='public')
    def index(self, **kw):
        _logger.debug("got %r", kw)
        if 'tokken' not in kw:
            return "Invalid tokken"
        if 'type' not in kw:
            return "Invalid type"
        _logger.debug("got %r", kw)
        # Do try to load phonebook with given tokken
        rpb_obj = http.request.env['remote.phonebook']
        _logger.debug("got %r", kw)
        rpb = rpb_obj.sudo().search([('tokken', '=', kw['tokken'])])
        _logger.debug("got %r", rpb)
        # if len(rpb) != 1:
        #     return "Tokken not registered"
        # _logger.debug("Content: %r", rpb.content)

        response = http.request.make_response(rpb._get_content_aastra(kw['type']), headers=[('Content-Type', 'text/xml')])
        return response

    @http.route('/aastra/phonebook/<type>/new_entry/1', auth='public')
    def new_entry(self, **kw):
        if 'type' not in kw:
            return "Invalid type"
        root = ET.Element('AastraIPPhoneInputScreen')
        cancel_action = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % "test"
        root.set('cancelAction', cancel_action)
        title = ET.SubElement(root, 'Title')
        title.text = "Neuer Kontakt"
        prompt = ET.SubElement(root, 'Prompt')
        prompt.text = "Name"
        parameter = ET.SubElement(root, 'Parameter')
        parameter.text = "name"
        url = ET.SubElement(root, 'URL')
        url.text = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/new_entry/2" % kw['type']
        response = http.request.make_response(
            ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes"),
            headers=[('Content-Type', 'text/xml')])
        return response

    @http.route('/aastra/phonebook/<type>/new_entry/2', auth='public')
    def new_entry_number(self, **kw):
        if 'type' not in kw:
            return "Invalid type"
        root = ET.Element('AastraIPPhoneInputScreen')
        cancel_action = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/new_entry/1" % kw['type']
        root.set('cancelAction', cancel_action)
        title = ET.SubElement(root, 'Title')
        title.text = kw['name']
        prompt = ET.SubElement(root, 'Prompt')
        prompt.text = "Nummer"
        parameter = ET.SubElement(root, 'Parameter')
        parameter.text = "number"
        url = ET.SubElement(root, 'URL')
        url.text = http.request.env['ir.config_parameter'].get_param(
            'web.base.url') + "aastra/phonebook/%s/new_entry/create/%s" % (kw['type'], kw['name'])
        response = http.request.make_response(
            ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes"),
            headers=[('Content-Type', 'text/xml')])
        return response

    @http.route('/aastra/phonebook/<type>/new_entry/create/<name>', auth='public')
    def new_entry_create(self, **kw):
        if 'type' not in kw:
            return "Invalid type"
        if 'name' not in kw:
            return "Invalid name"
        vals = {
            'name': kw['name'],
            'phone': kw['number'],
        }
        if kw['type'] == 'supplier':
            vals['supplier'] = True
        else:
            vals['customer'] = True
        http.request.env['res.partner'].sudo().create(vals)
        return redirect("/aastra/phonebook/test")

    @http.route('/aastra/phonebook/<type>/search_screen', auth='public')
    def search_screen(self, **kw):
        root = ET.Element('AastraIPPhoneInputScreen')
        cancel_action = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % "test"
        root.set('cancelAction', cancel_action)
        title = ET.SubElement(root, 'Title')
        title.text = "Suche"
        prompt = ET.SubElement(root, 'Prompt')
        prompt.text = "Suche"
        parameter = ET.SubElement(root, 'Parameter')
        parameter.text = "search"
        url = ET.SubElement(root, 'URL')
        url.text = http.request.env['ir.config_parameter'].get_param(
            'web.base.url') + "/aastra/phonebook/%s/search" % kw['type']
        response = http.request.make_response(
            ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes"),
            headers=[('Content-Type', 'text/xml')])
        return response

    @http.route('/aastra/phonebook/<type>/search', auth='public')
    def search(self, **kw):
        if 'search' not in kw:
            return "Invalid search parameter"
        persons = http.request.env['res.partner'].sudo().search([('name', 'ilike', kw['search'])])
        root = ET.Element('AastraIPPhoneTextMenu')
        cancel_action = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s" % "test"
        root.set('cancelAction', cancel_action)
        # root.set('wrap', 'no')
        title = ET.SubElement(root, 'Title')
        title.text = kw['search']
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Neuer Eintrag"
        uri = ET.SubElement(new, 'URI')
        uri.text = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/new_entry/1" % kw['type']
        new = ET.SubElement(root, 'MenuItem')
        name = ET.SubElement(new, 'Prompt')
        name.text = "Suche"
        uri = ET.SubElement(new, 'URI')
        uri.text = http.request.env['ir.config_parameter'].get_param('web.base.url') + "/aastra/phonebook/%s/search_screen" % kw['type']
        for partner in persons:
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
        response = http.request.make_response(
            ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes"),
            headers=[('Content-Type', 'text/xml')])
        return response

    @http.route('/aastra/incomming', auth='public')
    def incomming_call(self, **kw):
        number = kw.get('number', False)
        _logger.info("Incomming call from: %r", number)
        if not number:
            return "Invalid number"
        contact = http.request.env['res.partner'].sudo().search(['|', ('phone', '=', number), ('mobile', '=', number)])
        if contact:
            http.request.env['crm.phonecall'].sudo().create({
                'name': "Eingehender Anruf von %s" % contact.name,
                'partner_id': contact.id
            })
            root = ET.Element('AastraIPPhoneTextScreen')
            root.set('allowAnswer', 'yes')
            root.set('Timeout', '20')

            # root.set('wrap', 'no')
            message = ET.SubElement(root, 'Title')
            message.text = "Bekannter Kunde: %s" % str(contact.name)
            message = ET.SubElement(root, 'Text')
            message.text = "Bestellungen: %s - offene Kredite: %s - Umsatz: %s" % (str(contact.sale_order_count), str(contact.debt), str(contact.total_invoiced))
        else:
            http.request.env['crm.phonecall'].sudo().create({
                'name': "Eingehender Anruf von %s" % number,
            })
            root = ET.Element('AastraIPPhoneTextScreen')
            root.set('allowAnswer', 'yes')
            root.set('Timeout', '20')

            # root.set('wrap', 'no')
            message = ET.SubElement(root, 'Title')
            message.text = "Unbekannter Kunde: %s" % str(contact.name)
            message = ET.SubElement(root, 'Text')
            message.text = ""
        response = http.request.make_response(
            ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone="yes"),
            headers=[('Content-Type', 'text/xml')])
        return response