from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class VicidialWebhookController(http.Controller):

    # controllers/main.py
    @http.route('/vici/lead/<int:lead_id>', type='http', auth='user', csrf=False)
    def get_lead_info(self, lead_id, **kwargs):
        lead = request.env['crm.lead'].sudo().browse(lead_id)
        data = {
            "id": lead.id,
            "name": lead.name,
            "company_name": lead.partner_name,
            "contact_name": lead.contact_name,
            "email": lead.email_from,
            "phone": lead.phone,
        }
        return http.Response(
            json.dumps(data),
            content_type='application/json;charset=utf-8'
        )


    @http.route('/vici/webhook', type='http', auth='public', methods=['POST', 'GET'], csrf=False)
    def vicidial_webhook(self, **post):
        try:
            # 1. Detect and parse incoming data
            if request.httprequest.content_type == 'application/json':
                data = json.loads(request.httprequest.data.decode('utf-8'))
            else:
                data = dict(request.params)

            

            # 2. Extract key fields

            phone = data.get('phone_number')
            sip_exten = data.get('SIPexten')


            # def get_campaign_id(campaign_name):
            #     if not campaign_name:
            #         return None
            #     campaign = request.env['crm.campaign'].search([('name', '=', campaign_name)], limit=1)
            #     return campaign.id if campaign else None
           
           
            def get_country_id(country_code):
                if not country_code:
                    return None
                country = request.env['res.country'].search([('code', '=', country_code.upper())], limit=1)
                return country.id if country else None

             # 3. Match user by Vicidial extension
            user = request.env['res.users'].sudo().search([
                ('vicidial_extension', '=', sip_exten)
            ], limit=1)
            if not user:
                return http.Response(
                    json.dumps({'status': 'error', 'message': 'User not found'}),
                    content_type='application/json'
                )
            lead_vals = {
                'vicidial_lead_id': data.get('lead_id'),
                'name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or data.get('fullname', 'Unnamed Lead'),
                'contact_name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                'phone': data.get('phone_number'),
                'mobile': data.get('alt_phone'),
                'email_from': data.get('email'),
                'street': data.get('address1'),
                'city': data.get('city'),
                'zip': data.get('postal_code'),
                'description': data.get('comments') or f"Recording: {data.get('recording_filename', '')}",
                #'campaign_id': get_campaign_id(data.get('campaign')),  # map to campaign record ID or None
                'country_id': get_country_id(data.get('country_code')),  # map to country record ID or None
                'user_id': user.id,  # map to user record ID or None
            }
            

            # 4. Get or create iframe session for user
            iframe = request.env['custom.iframe'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            if iframe:
               #domain = [('phone', '=', phone)]
                domain = ['|', ('phone', '=', phone), ('vicidial_lead_id', '=', data.get('lead_id'))]
                leads = request.env['crm.lead'].sudo().search(domain)
                if leads: 
                    iframe.sudo().write({'lead_ids': [(6, 0, leads.ids)]})
                else:
                    new_lead = request.env['crm.lead'].sudo().create(lead_vals)
                    iframe.sudo().write({'lead_ids': [(4, new_lead.id)]})

            
            return http.Response(
                json.dumps({'status': 'success', 'iframe_id': iframe.id, 'lead_ids':str(iframe.lead_ids), 'phone':phone}),
                content_type='application/json'
            )

        except Exception as e:
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json'
            )

    @http.route('/custom_iframe/create_on_load', type='json', auth='user')
    def create_iframe_on_load(self):
        # Create a record when the view is opened
        iframe = request.env['custom.iframe'].sudo().create({
            'user_id': request.env.user.id,
        })
        request.session['iframe_id'] = iframe.id
        return {'status': 'created'}

    @http.route('/custom_iframe/delete_on_unload', type='json', auth='user')
    def delete_iframe_on_unload(self):
        iframe_id = request.session.get('iframe_id')
        if iframe_id:
            record = request.env['custom.iframe'].sudo().browse(iframe_id)
            if record.exists():
                record.unlink()
                request.session['iframe_id'] = None
        return {'status': 'deleted'}
    
    @http.route('/vici/iframe/session', type='http', auth='user', methods=['GET'], csrf=False)
    def get_iframe_data(self, **kwargs):
        try:
            sip_exten = kwargs.get('sip_exten')
            user_id = kwargs.get('user_id')
            _logger.info("sip_exten %s", sip_exten)
            _logger.info("userID %s" , user_id)
            _logger.info("env user ID %s", request.env.user.id)
            _logger.info("env user vicidial %s", request.env.user.vicidial_extension)

            domain = []
            if user_id:
                domain.append(('id', '=', request.env.user.id))
            # elif sip_exten:
            #     domain.append(('vicidial_extension', '=', str(sip_exten)))
            else:
                domain.append(('id', '=', int(user_id)))
            _logger.info("domain....?? %s", domain)
            user = request.env['res.users'].sudo().search(domain, limit=1)
            _logger.info("user id >>> %s",user.id)
            if not user:
                return http.Response(
                    json.dumps({'status': 'error', 'message': 'User not found'}),
                    content_type='application/json'
                )
            iframe = request.env['custom.iframe'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            if not iframe:
                return http.Response(
                    json.dumps({'status': 'error', 'message': 'No iframe session found'}),
                    content_type='application/json'
                )
            leads_data = []
            for lead in iframe.lead_ids:
                # Safely get partner name
                partner_name = None
                if hasattr(lead, 'partner_name') and lead.partner_name:
                    if hasattr(lead.partner_name, 'name'):
                        partner_name = lead.partner_name.name
                    else:
                        partner_name = str(lead.partner_name)
                
                # Safely get stage name
                stage_name = None
                if hasattr(lead, 'stage_id') and lead.stage_id:
                    if hasattr(lead.stage_id, 'name'):
                        stage_name = lead.stage_id.name
                    else:
                        stage_name = str(lead.stage_id)
                
                # Safely get user name  
                user_name = None
                if hasattr(lead, 'user_id') and lead.user_id:
                    if hasattr(lead.user_id, 'name'):
                        user_name = lead.user_id.name
                    else:
                        user_name = str(lead.user_id)
                
                # Safely get company name
                company_name = None
                if hasattr(lead, 'company_id') and lead.company_id:
                    if hasattr(lead.company_id, 'name'):
                        company_name = lead.company_id.name
                    else:
                        company_name = str(lead.company_id)

                leads_data.append({
                    'id': lead.id,
                    'opportunity': lead.name or '',
                    'company_name': partner_name,
                    'phone': lead.phone or '',
                    'email': lead.email_from or '',
                    'stage': stage_name,
                    'sales_person': user_name,
                    'priority': getattr(lead, 'priority', ''),
                    'revenue': getattr(lead, 'expected_revenue', 0),
                    'create_date': lead.create_date.strftime('%Y-%m-%d %H:%M:%S') if lead.create_date else '',
                    'company_id': company_name,
                    'iframe_id': lead.iframe_id.id if hasattr(lead, 'iframe_id') and lead.iframe_id else None,
                })
            _logger.info("leads data is %s", leads_data)
            return http.Response(
                json.dumps({
                    'status': 'success',
                    'iframe_id': iframe.id,
                    'lead_ids': leads_data,
                    'user': user.name
                }),
                content_type='application/json'
            )

        except Exception as e:
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json'
            )