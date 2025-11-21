# controllers.py
import logging
from odoo import http
from odoo.http import request
import json

_logger = logging.getLogger(__name__)

class WebsiteLeadsController(http.Controller):
    ROUTE = "/api/website-leads"

    @http.route(ROUTE, type="json", auth="public", methods=["POST"], csrf=False)
    def receive_website_lead(self, **kwargs):
        _logger.info("**********Website Lead API HIT**********")

        data = json.loads(request.httprequest.data.decode())


        service = data.get("service")
        

        # Dispatch to handlers
        handler_map = {
            "credit_card_website": self._handle_credit_card_website,
            "energy_website": self._handle_energy_website,
            "optus_nbn_website": self._handle_optus_nbn_website,
        }

        handler = handler_map.get(service)
        if not handler:
            return {"status": "error", "message": f"No handler for service: {service}"}

        return handler(data)

    # --- Handlers ---
    def _handle_credit_card_website(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}
        customer = payload.get("customer", {})
        revenue = payload.get("revenue", {})
        consents = payload.get("consents", {})

        # 1) Create CRM Lead
        lead_vals = {
            "name": f"{customer.get('firstName','')} {customer.get('lastName','')}".strip() or "Credit Card Lead",
            "contact_name": f"{customer.get('firstName','')} {customer.get('lastName','')}".strip(),
            "phone": customer.get("phone"),
            "email_from": customer.get("email"),
            "services": "credit_card_website",
            "lead_for": "credit_card_website",
            "lead_stage": "2",
            "unlock_stage_1": False,
            "stage_id":stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # 2) Create Stage-1 Form Record
        form_vals = {
            "id": lead.id,
            "lead_stage": "1",

            # Customer Details
            "cc_prefix": customer.get("prefix"),
            "cc_first_name": customer.get("firstName"),
            "cc_last_name": customer.get("lastName"),
            "cc_job_title": customer.get("jobTitle"),
            "cc_phone": customer.get("phone"),
            "cc_email": customer.get("email"),
            "cc_address": customer.get("address"),

            # Revenue Details
            "cc_annual_revenue": revenue.get("annualRevenue"),
            "cc_annual_spend": revenue.get("annualSpend"),
            "cc_existing_products": revenue.get("existingProducts"),
            "cc_expense_tools": revenue.get("expenseTools"),

            # Consents
            "cc_consent_personal_info": consents.get("personalInfo"),
            "cc_consent_contact_method": consents.get("contactMethod"),
            "cc_contact_preference": consents.get("contactPreference"),

            # Notes
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(form_vals)

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Credit card website lead created successfully",
        }

    def _handle_energy_website(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        customer = payload.get("customer", {})  
        property = payload.get("property",{})
        currentProviders = payload.get("currentProviders",{})
        serviceRequirements = payload.get("serviceRequirements",{})
        usageInformation = payload.get("usageInformation",{})
        preferencesAndConsents = payload.get("preferencesAndConsents",{})
        preferencesAndConsents = payload.get("preferencesAndConsents",{})
        
        lead_vals = {
            "name": (
                f"{customer.get('firstName', '').strip()} {customer.get('lastName', '').strip()}" 
                or customer.get('name', '').strip() 
                or "Electricty and Gas Lead"
            ),
            "phone": customer.get("phone"),
            "email_from": customer.get("email"),
            "services": "energy_website",  # change to "energy_website" if needed
            "lead_for": "energy_website",  # same as above
            "lead_stage": "2",
            "unlock_stage_1": False,
            "stage_id": stage.id,                # ensure stage is fetched above
        }

        lead = request.env["crm.lead"].sudo().create(lead_vals)
        lead_vals = {
            "en_name": customer.get("name"),
            "en_contact_number": customer.get("contactNumber"),
            "en_email": customer.get("email"),
            "en_current_address": customer.get("currentAddress"),
            "en_property_type": property.get("propertyType"),
            "en_property_ownership": property.get("propertyOwnership"),
            "en_what_to_compare": property.get("whatToCompare"),
            "en_moving_in": property.get("movingIn"),
            "en_date": property.get("movingInDate"),
            "en_electricity_provider": currentProviders.get("electricityProvider"),
            "en_gas_provider": currentProviders.get("gasProvider"),
            "en_rooftop_solar": serviceRequirements.get("rooftopSolar"),
            "en_require_life_support": serviceRequirements.get("requireLifeSupport"),
            "en_concesion_card_holder": serviceRequirements.get("concessionCardHolder"),
            "type_of_concession": serviceRequirements.get("typeOfConcession"),
            "en_usage_profile": usageInformation.get("usageProfile"),
            "en_request_callback": preferencesAndConsents.get("requestCallback"),
            "en_accpeting_terms": preferencesAndConsents.get("acceptingTerms"),
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(lead_vals)

        return {"status": "success", "lead_id": lead.id, "message": "Energy website lead created"}

    def _handle_optus_nbn_website(self, payload):
        lead_vals = {
            "name": payload.get("name"),
            "contact_name": payload.get("name"),
            "phone": payload.get("phone"),
            "email_from": payload.get("email"),
            "services": "optus_nbn_website",
            "lead_for": "optus_nbn_website",
            "lead_source": "website",
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)
        return {"status": "success", "lead_id": lead.id, "message": "NBN website lead created"}
