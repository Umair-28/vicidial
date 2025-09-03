import json
import logging
from odoo import http
from odoo.http import request
from datetime import datetime

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

    @http.route('/vici/test', type='http', auth='public', methods=['GET'], csrf=False)
    def vici_test(self, **kwargs):
        return "✅ Vici webhook test route is working!"    

    @http.route('/vici/webhook', type='json', auth='public', methods=['POST'], csrf=False, cors="*")
    def vicidial_webhook(self, **kwargs):
        try:
            request.session.sid = False
            request.session.should_save = False
            _logger.info("✅ API HITTED......")

            # 1. Parse JSON payload
            try:
                raw_body = request.httprequest.data
                data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except Exception as parse_err:
                _logger.error("❌ Failed to parse JSON: %s", str(parse_err))
                return {"status": "error", "message": "Invalid JSON payload"}

            leads = data.get("leads", [])
            agent = data.get("agent")
            extension = data.get("extension", "SIP/8011")
            env = request.env(su=True)

            # 2. Handle empty leads -> delete records
            if not leads:
                _logger.warning("⚠️ No leads found in payload. Deleting vicidial records for extension=%s", extension)
                
                # 🎯 SIMPLE FIX: Only delete vicidial leads
                vicidial_leads = request.env["vicidial.lead"].sudo().search([("extension", "=", extension)])
                deleted_count = len(vicidial_leads)
                vicidial_leads.unlink()
                
                _logger.info("✅ Deleted %d vicidial leads, CRM leads preserved", deleted_count)
                
                return {
                    "status": "success",
                    "message": "Deleted {} vicidial leads for extension {}".format(deleted_count, extension)
                }

            _logger.info("📩 Processing %s leads for agent=%s, extension=%s", len(leads), agent, extension)

            created_records = []
            default_stage = request.env['crm.stage'].sudo().search([('name', '=', 'New')], limit=1)
            if not default_stage:
                default_stage = request.env['crm.stage'].sudo().create({'name': 'New'})

            _logger.info("Default stage is %s", default_stage)    

            # 3. Iterate and create/update records
            for lead in leads:
                try:
                    # Correctly parse the datetime fields
                    entry_date_str = lead.get("entry_date")
                    modify_date_str = lead.get("modify_date")
                    last_local_call_time_str = lead.get("last_local_call_time")

                    entry_date_obj = datetime.strptime(entry_date_str, '%Y-%m-%dT%H:%M:%S') if entry_date_str else False
                    modify_date_obj = datetime.strptime(modify_date_str, '%Y-%m-%dT%H:%M:%S') if modify_date_str else False
                    last_local_call_time_obj = datetime.strptime(last_local_call_time_str, '%Y-%m-%dT%H:%M:%S') if last_local_call_time_str else False
                    
                    # 🎯 FIX: Search by lead_id instead of duplicating the search
                    VicidialLead = request.env["vicidial.lead"].sudo()
                    existing_vicidial_lead = VicidialLead.search([("lead_id", "=", str(lead.get("lead_id")))], limit=1)
                    
                    # Common values for vicidial records
                    vicidial_vals = {
                        "lead_id": str(lead.get("lead_id")),
                        "status": lead.get("status"),
                        "entry_date": entry_date_obj,
                        "modify_date": modify_date_obj,
                        "agent_user": agent,
                        "extension": extension,
                        "user": lead.get("user"),
                        "vendor_lead_code": lead.get("vendor_lead_code"),
                        "source_id": lead.get("source_id"),
                        "list_id": str(lead.get("list_id")) if lead.get("list_id") else False,
                        "gmt_offset_now": lead.get("gmt_offset_now"),
                        "called_since_last_reset": str(lead.get("called_since_last_reset")).upper() in ["Y", "1", "TRUE"],
                        "phone_code": lead.get("phone_code"),
                        "phone_number": lead.get("phone_number"),
                        "title": lead.get("title"),
                        "first_name": lead.get("first_name"),
                        "middle_initial": lead.get("middle_initial"),
                        "last_name": lead.get("last_name"),
                        "address1": lead.get("address1"),
                        "address2": lead.get("address2"),
                        "address3": lead.get("address3"),
                        "city": lead.get("city"),
                        "state": lead.get("state"),
                        "province": lead.get("province"),
                        "postal_code": lead.get("postal_code"),
                        "country_code": lead.get("country_code"),
                        "gender": lead.get("gender") if lead.get("gender") in ["M", "F", "O"] else False,
                        "date_of_birth": lead.get("date_of_birth"),
                        "alt_phone": lead.get("alt_phone"),
                        "email": lead.get("email"),
                        "security_phrase": lead.get("security_phrase"),
                        "comments": lead.get("comments"),
                        "called_count": lead.get("called_count"),
                        "last_local_call_time": last_local_call_time_obj,
                        "rank": lead.get("rank"),
                        "owner": lead.get("owner"),
                        "entry_list_id": str(lead.get("entry_list_id")),
                        # 🎯 FIX: Remove fields that don't belong to vicidial.lead model
                        # "companyName": "K N K TRADERS",  # This belongs to CRM lead
                        # "stage_id": default_stage.id,    # This belongs to CRM lead
                    }
                    
                    # 🎯 FIX: Proper CRM lead values
                    crm_vals = {
                        'name': lead.get('first_name', '') + (' ' + lead.get('last_name', '')).strip() or lead.get('comments', 'Unnamed Lead'),
                        'partner_name': 'K N K TRADERS',
                        'phone': lead.get('phone_number'),
                        'stage_id': default_stage.id,
                        'description': lead.get('comments'),
                        'vicidial_lead_id': None,  # Will be set below
                    }
                    
                    if not existing_vicidial_lead:
                        # ========== CREATING NEW LEAD ==========
                        _logger.info("📝 Creating new lead with lead_id: %s", lead.get("lead_id"))
                        
                        # Step 1: Create Vicidial lead first
                        vicidial_rec = VicidialLead.create(vicidial_vals)
                        _logger.info("✅ Created vicidial lead with ID: %s", vicidial_rec.id)
                        
                        # Step 2: Set the vicidial_lead_id in CRM vals
                        crm_vals['vicidial_lead_id'] = vicidial_rec.id  # Use the actual vicidial record ID
                        
                        # Step 3: Create CRM lead
                        crm_lead_rec = request.env['crm.lead'].sudo().create(crm_vals)
                        _logger.info("✅ Created CRM lead with ID: %s", crm_lead_rec.id)
                        
                        # Step 4: Link CRM lead back to Vicidial record
                        vicidial_rec.write({'crm_lead_id': crm_lead_rec.id})
                        _logger.info("🔗 Linked vicidial lead %s to CRM lead %s", vicidial_rec.id, crm_lead_rec.id)
                        
                        created_records.append(vicidial_rec.id)

                    else:
                        # ========== UPDATING EXISTING LEAD ==========
                        _logger.info("📝 Updating existing lead with lead_id: %s", lead.get("lead_id"))
                        
                        # Step 1: Update Vicidial record
                        existing_vicidial_lead.write(vicidial_vals)
                        _logger.info("✅ Updated vicidial lead ID: %s", existing_vicidial_lead.id)
                        
                        # Step 2: Handle CRM lead
                        if existing_vicidial_lead.crm_lead_id:
                            # Update existing CRM lead
                            crm_vals['vicidial_lead_id'] = existing_vicidial_lead.id  # Ensure consistency
                            existing_vicidial_lead.crm_lead_id.sudo().write(crm_vals)
                            _logger.info("✅ Updated existing CRM lead ID: %s", existing_vicidial_lead.crm_lead_id.id)
                        else:
                            # Create missing CRM lead
                            _logger.warning("⚠️ CRM lead missing for vicidial lead %s, creating new one", existing_vicidial_lead.id)
                            crm_vals['vicidial_lead_id'] = existing_vicidial_lead.id
                            crm_lead_rec = request.env['crm.lead'].sudo().create(crm_vals)
                            existing_vicidial_lead.write({'crm_lead_id': crm_lead_rec.id})
                            _logger.info("✅ Created and linked new CRM lead ID: %s", crm_lead_rec.id)
                        
                        created_records.append(existing_vicidial_lead.id)

                except Exception as lead_error:
                    _logger.error("❌ Error processing lead %s: %s", lead.get("lead_id"), str(lead_error))
                    continue

            _logger.info("✅ Successfully processed %s leads", len(created_records))

            return {
                "status": "success",
                "created_records": created_records,
                "message": "{} leads processed successfully".format(len(created_records))
            }

        except Exception as e:
            _logger.error("❌ Critical error in webhook: %s", str(e))
            import traceback
            _logger.error("Full traceback: %s", traceback.format_exc())
            return {"status": "error", "message": str(e)}



    # @http.route('/vici/webhook', type='http', auth='public', methods=['POST', 'GET'], csrf=False)
    # def vicidial_webhook(self, **post):
    #     try:
    #         # 1. Detect and parse incoming data
    #         if request.httprequest.content_type == 'application/json':
    #             data = json.loads(request.httprequest.data.decode('utf-8'))
    #         else:
    #             data = dict(request.params)

            

    #         # 2. Extract key fields

    #         phone = data.get('phone_number')
    #         sip_exten = data.get('SIPexten')


    #         # def get_campaign_id(campaign_name):
    #         #     if not campaign_name:
    #         #         return None
    #         #     campaign = request.env['crm.campaign'].search([('name', '=', campaign_name)], limit=1)
    #         #     return campaign.id if campaign else None
           
           
    #         def get_country_id(country_code):
    #             if not country_code:
    #                 return None
    #             country = request.env['res.country'].search([('code', '=', country_code.upper())], limit=1)
    #             return country.id if country else None

    #          # 3. Match user by Vicidial extension
    #         user = request.env['res.users'].sudo().search([
    #             ('vicidial_extension', '=', sip_exten)
    #         ], limit=1)
    #         if not user:
    #             return http.Response(
    #                 json.dumps({'status': 'error', 'message': 'User not found'}),
    #                 content_type='application/json'
    #             )
    #         lead_vals = {
    #             'vicidial_lead_id': data.get('lead_id'),
    #             'name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or data.get('fullname', 'Unnamed Lead'),
    #             'contact_name': f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
    #             'phone': data.get('phone_number'),
    #             'mobile': data.get('alt_phone'),
    #             'email_from': data.get('email'),
    #             'street': data.get('address1'),
    #             'city': data.get('city'),
    #             'zip': data.get('postal_code'),
    #             'description': data.get('comments') or f"Recording: {data.get('recording_filename', '')}",
    #             #'campaign_id': get_campaign_id(data.get('campaign')),  # map to campaign record ID or None
    #             'country_id': get_country_id(data.get('country_code')),  # map to country record ID or None
    #             'user_id': user.id,  # map to user record ID or None
    #         }
            

    #         # 4. Get or create iframe session for user
    #         iframe = request.env['custom.iframe'].sudo().search([
    #             ('user_id', '=', user.id)
    #         ], limit=1)
    #         if iframe:
    #            #domain = [('phone', '=', phone)]
    #             domain = ['|', ('phone', '=', phone), ('vicidial_lead_id', '=', data.get('lead_id'))]
    #             leads = request.env['crm.lead'].sudo().search(domain)
    #             if leads: 
    #                 iframe.sudo().write({'lead_ids': [(6, 0, leads.ids)]})
    #             else:
    #                 new_lead = request.env['crm.lead'].sudo().create(lead_vals)
    #                 iframe.sudo().write({'lead_ids': [(4, new_lead.id)]})

            
    #         return http.Response(
    #             json.dumps({'status': 'success', 'iframe_id': iframe.id, 'lead_ids':str(iframe.lead_ids), 'phone':phone}),
    #             content_type='application/json'
    #         )

    #     except Exception as e:
    #         return http.Response(
    #             json.dumps({'status': 'error', 'message': str(e)}),
    #             content_type='application/json'
    #         )

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
    
    # @http.route('/vici/iframe/session', type='http', auth='user', methods=['GET'], csrf=False)
    # def get_iframe_data(self, **kwargs):
    #     try:
    #         sip_exten = kwargs.get('sip_exten')
    #         user_id = kwargs.get('user_id')
    #         # _logger.info("sip_exten %s", sip_exten)
    #         # _logger.info("userID %s" , user_id)
    #         # _logger.info("env user ID %s", request.env.user.id)
    #         # _logger.info("env user vicidial %s", request.env.user.vicidial_extension)

    #         domain = []
    #         if user_id:
    #             domain.append(('id', '=', int(user_id)))
    #         elif sip_exten:
    #             domain.append(('vicidial_extension', '=', str(sip_exten)))
    #         else:
    #             domain.append(('id', '=', request.env.user.id))
    #         # _logger.info("domain....?? %s", domain)
    #         user = request.env['res.users'].sudo().search(domain, limit=1)
    #         # _logger.info("user id >>> %s",user.id)
    #         # _logger.info("user vicidial_entension is  >>> %s",user.vicidial_extension)

    #         if not user:
    #             return http.Response(
    #                 json.dumps({'status': 'error', 'message': 'User not found'}),
    #                 content_type='application/json'
    #             )
    #         iframe = request.env['custom.iframe'].sudo().search([
    #             ('user_id', '=', user.id)
    #         ], limit=1)
    #         if not iframe:
    #             return http.Response(
    #                 json.dumps({'status': 'error', 'message': 'No iframe session found'}),
    #                 content_type='application/json'
    #             )
    #         leads_data = []
    #         for lead in iframe.lead_ids:
    #             # Safely get partner name
    #             partner_name = None
    #             if hasattr(lead, 'partner_name') and lead.partner_name:
    #                 if hasattr(lead.partner_name, 'name'):
    #                     partner_name = lead.partner_name.name
    #                 else:
    #                     partner_name = str(lead.partner_name)
                
    #             # Safely get stage name
    #             stage_name = None
    #             if hasattr(lead, 'stage_id') and lead.stage_id:
    #                 if hasattr(lead.stage_id, 'name'):
    #                     stage_name = lead.stage_id.name
    #                 else:
    #                     stage_name = str(lead.stage_id)
                
    #             # Safely get user name  
    #             user_name = None
    #             if hasattr(lead, 'user_id') and lead.user_id:
    #                 if hasattr(lead.user_id, 'name'):
    #                     user_name = lead.user_id.name
    #                 else:
    #                     user_name = str(lead.user_id)
                
    #             # Safely get company name
    #             company_name = None
    #             if hasattr(lead, 'company_id') and lead.company_id:
    #                 if hasattr(lead.company_id, 'name'):
    #                     company_name = lead.company_id.name
    #                 else:
    #                     company_name = str(lead.company_id)

    #             leads_data.append({
    #                 'id': lead.id,
    #                 'opportunity': lead.name or '',
    #                 'company_name': partner_name,
    #                 'phone': lead.phone or '',
    #                 'email': lead.email_from or '',
    #                 'stage': stage_name,
    #                 'sales_person': user_name,
    #                 'priority': getattr(lead, 'priority', ''),
    #                 'revenue': getattr(lead, 'expected_revenue', 0),
    #                 'create_date': lead.create_date.strftime('%Y-%m-%d %H:%M:%S') if lead.create_date else '',
    #                 'company_id': company_name,
    #                 'iframe_id': lead.iframe_id.id if hasattr(lead, 'iframe_id') and lead.iframe_id else None,
    #             })
    #         # _logger.info("leads data is %s", leads_data)
    #         return http.Response(
    #             json.dumps({
    #                 'status': 'success',
    #                 'iframe_id': iframe.id,
    #                 'lead_ids': leads_data,
    #                 'user': user.name
    #             }),
    #             content_type='application/json'
    #         )

    #     except Exception as e:
    #         return http.Response(
    #             json.dumps({'status': 'error', 'message': str(e)}),
    #             content_type='application/json'
    #         )

    @http.route('/vici/iframe/session', type='http', auth='user', methods=['GET'], csrf=False)
    def get_iframe_data(self, **kwargs):
        try:
            # ✅ Hardcoded extension (later replace with kwargs.get('sip_exten'))
            extension = "SIP/8011"

            # 1. Fetch leads from vicidial.lead model
            leads = request.env['vicidial.lead'].sudo().search([('extension', '=', extension)], order='id desc')
            _logger.info("Found %d leads for extension %s", len(leads), extension)

            leads_data = []
            for lead in leads:
                try:
                    # 🎯 CRITICAL: Get CRM lead information for proper linking
                    crm_lead_id = None
                    stage_id = None
                    stage_name = "New"
                    
                    if lead.crm_lead_id:
                        crm_lead_id = lead.crm_lead_id.id
                        if lead.crm_lead_id.stage_id:
                            stage_id = lead.crm_lead_id.stage_id.id
                            stage_name = lead.crm_lead_id.stage_id.name
                    
                    # If no stage from CRM lead, get default
                    if not stage_id:
                        default_stage = request.env['crm.stage'].sudo().search([('name', '=', 'New')], limit=1)
                        if default_stage:
                            stage_id = default_stage.id
                            stage_name = default_stage.name

                    lead_data = {
                        # 🎯 CRITICAL FIELDS for JavaScript functionality
                        "id": lead.id,  # This is the Vicidial lead ID that JavaScript will use
                        "crm_lead_id": crm_lead_id,  # Link to CRM lead
                        "stage_id": stage_id,
                        "stage_name": stage_name,
                        "companyName": "K N K TRADERS",  # Required by renderer
                        
                        # All your existing fields
                        "province": lead.province or "",
                        "last_name": lead.last_name or "",
                        "alt_phone": lead.alt_phone or "",
                        "phone_code": lead.phone_code or "",
                        "last_local_call_time": lead.last_local_call_time.strftime('%Y-%m-%d %H:%M:%S') if lead.last_local_call_time else "",
                        "rank": lead.rank or 0,
                        "postal_code": lead.postal_code or "",
                        "country_code": lead.country_code or "",
                        "owner": lead.owner or "",
                        "middle_initial": lead.middle_initial or "",
                        "vendor_lead_code": lead.vendor_lead_code or "",
                        "first_name": lead.first_name or "",
                        "title": lead.title or "",
                        "comments": lead.comments or "",
                        "gmt_offset_now": lead.gmt_offset_now or 0.0,
                        "state": lead.state or "",
                        "date_of_birth": lead.date_of_birth.strftime('%Y-%m-%d') if lead.date_of_birth else None,
                        "entry_date": lead.entry_date.strftime('%Y-%m-%d %H:%M:%S') if lead.entry_date else "",
                        "list_id": lead.list_id or "",
                        "phone_number": lead.phone_number or "",
                        "email": lead.email or "",
                        "status": lead.status or "",
                        "called_since_last_reset": lead.called_since_last_reset or "",
                        "city": lead.city or "",
                        "address1": lead.address1 or "",
                        "address2": lead.address2 or "",
                        "address3": lead.address3 or "",
                        "user": lead.user or "",
                        "entry_list_id": lead.entry_list_id or "",
                        "lead_id": lead.lead_id or "",  # This is the external Vicidial system ID
                        "gender": lead.gender or "",
                        "called_count": lead.called_count or 0,
                        "modify_date": lead.modify_date.strftime('%Y-%m-%d %H:%M:%S') if lead.modify_date else "",
                        "source_id": lead.source_id or "",
                        "security_phrase": lead.security_phrase or "",
                        "extension": lead.extension or "",
                        "agent_user": lead.agent_user or "",
                    }
                    
                    leads_data.append(lead_data)
                    
                except Exception as lead_error:
                    _logger.error("Error processing lead ID %s: %s", lead.id, str(lead_error))
                    continue

            _logger.info("Successfully processed %d leads", len(leads_data))

            return http.Response(
                json.dumps({
                    'status': 'success',
                    'extension': extension,
                    'total_leads': len(leads_data),
                    'leads': leads_data
                }),
                content_type='application/json'
            )

        except Exception as e:
            _logger.error("Error in get_iframe_data: %s", str(e))
            return http.Response(
                json.dumps({'status': 'error', 'message': str(e)}),
                content_type='application/json'
            )