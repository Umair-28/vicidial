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
            "home_moving":self._handle_home_moving,
            "business_loan":self._handle_business_loan
        }

        handler = handler_map.get(service)
        if not handler:
            return {"status": "error", "message": f"No handler for service: {service}"}

        return handler(data)

    # --- Handlers --- #

    def _handle_credit_card_website(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}
        customer = payload.get("customer", {})
        revenue = payload.get("revenue", {})
        consents = payload.get("consents", {})
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
        form_vals = {
            "id": lead.id,
            "lead_stage": "2",
            "cc_prefix": customer.get("prefix"),
            "cc_first_name": customer.get("firstName"),
            "cc_last_name": customer.get("lastName"),
            "cc_job_title": customer.get("jobTitle"),
            "cc_phone": customer.get("phone"),
            "cc_email": customer.get("email"),
            "cc_address": customer.get("address"),
            "cc_annual_revenue": revenue.get("annualRevenue"),
            "cc_annual_spend": revenue.get("annualSpend"),
            "cc_existing_products": revenue.get("existingProducts"),
            "cc_expense_tools": revenue.get("expenseTools"),
            "cc_consent_personal_info": consents.get("personalInfo"),
            "cc_consent_contact_method": consents.get("contactMethod"),
            "cc_contact_preference": consents.get("contactPreference"),
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
            "services": "energy_website", 
            "lead_for": "energy_website",  
            "lead_stage": "2",
            "unlock_stage_1": False,
            "stage_id": stage.id,                
        }

        lead = request.env["crm.lead"].sudo().create(lead_vals)
        form_vals = {
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
        lead.sudo().write(form_vals)

        return {"status": "success", "lead_id": lead.id, "message": "Energy website lead created"}


    def _handle_optus_nbn_website(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        address = payload.get("address", {})
        preferences = payload.get("preferences", {})
        usage = payload.get("usageDetails", {})
        contact = payload.get("contact", {})
        agreement = payload.get("agreement", {})    
        lead_vals = {
            "name": (
                f"{contact.get('firstName', '').strip()} {contact.get('lastName', '').strip()}" 
                or contact.get('name', '').strip() 
                or "Optus NBN Lead"
            ),
            "contact_name": f"{contact.get('firstName','')} {contact.get('lastName','')}".strip() or "",
            "phone": contact.get("phone"),
            "email_from": contact.get("email"),
            "services": "optus_nbn_website",
            "lead_for": "optus_nbn_website",
            "lead_stage": "2",
            "unlock_stage_1": False,
            "stage_id":stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)
        form_vals = {
            "in_current_address": address.get("currentAddress"),
            "in_important_feature": preferences.get("importantFeature"),
            "in_speed_preference": preferences.get("speedPreference"),
            "in_broadband_reason": preferences.get("broadbandReason"),
            "in_when_to_connect_type": preferences.get("whenToConnectType"),
            "in_when_to_connect_date": preferences.get("whenToConnectDate"),
            "in_internet_users_count": usage.get("internetUsersCount"),
            "in_internet_usage_type": usage.get("internetUsageType"),
            "in_compare_plans": usage.get("comparePlans"),
            "in_name": contact.get("name"),
            "in_contact_number": contact.get("contactNumber"),
            "in_email": contact.get("email"),
            "in_accept_terms": agreement.get("acceptTerms"),
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(form_vals)
        return {"status": "success", "lead_id": lead.id, "message": "NBN website lead created"}

    def _handle_home_moving(self,payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        moving = payload.get("movingInformation", {})
        propertyContact = payload.get("propertyContact", {})
        personal = payload.get("personalInformation", {})
        contact = payload.get("contactInformation", {})
        referral = payload.get("referralMarketing", {})
        services = payload.get("servicesToConnect", {})    

        lead_vals = {
            "name": (
                f"{personal.get('firstName', '').strip()} {personal.get('lastName', '').strip()}" 
                or personal.get('name', '').strip() 
                or "Home Moving Lead"
            ),
            "contact_name": f"{contact.get('firstName','')} {contact.get('lastName','')}".strip() or "",
            "phone": contact.get("mobile"),
            "email_from": contact.get("email"),
            "services": "home_moving",
            "lead_for": "home_moving",
            "lead_stage": "2",
            "unlock_stage_1": False,
            "stage_id":stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)  
        form_vals = {
            "hm_moving_date": moving.get("movingDate"),
            "hm_address": moving.get("address"),
            "hm_property_type": moving.get("propertyType"),
            "hm_ownership": moving.get("ownership"),
            "hm_agency_name": propertyContact.get("agencyName"),
            "hm_broker_name": propertyContact.get("brokerName"),
            "hm_agency_contact_number": propertyContact.get("agencyContactNumber"),
            "hm_status": personal.get("status"),
            "hm_first_name": personal.get("firstName"),
            "hm_last_name": personal.get("lastName"),
            "hm_job_title": personal.get("jobTitle"),
            "hm_dob": personal.get("dob"),
            "hm_mobile": contact.get("mobile"),
            "hm_work_phone": contact.get("workPhone"),
            "hm_home_phone": contact.get("homePhone"),
            "hm_email": contact.get("email"),
            "hm_friend_code": referral.get("friendCode"),
            "hm_how_heard": referral.get("howHeard"),
            "hm_connect_electricity": services.get("electricity"),
            "hm_connect_gas": services.get("gas"),
            "hm_connect_internet": services.get("internet"),
            "hm_connect_water": services.get("water"),
            "hm_connect_tv": services.get("tv"),
            "hm_connect_removalist": services.get("removalist"),
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(form_vals)
        return {"status": "success", "lead_id": lead.id, "message": "Home Moving website lead created"}



    def _handle_business_loan(self,payload):
            stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
            if not stage:
                return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

            loan_info = payload.get("loanInformation",{})
            business = payload.get("businessDetails",{})
            applicant = payload.get("applicantInformation",{})
            consent = payload.get("consent",{})

            lead_vals = {
                "name": (
                    f"{applicant.get('firstName', '').strip()} {applicant.get('lastName', '').strip()}" 
                    or applicant.get('name', '').strip() 
                    or "Business Loan Lead"
                ),
                "contact_name": f"{applicant.get('firstName','')} {applicant.get('lastName','')}".strip() or "",
                "phone": applicant.get("mobile"),
                "email_from": applicant.get("email"),
                "services": "business_loan",
                "lead_for": "business_loan",
                "lead_stage": "2",
                "unlock_stage_1": False,
                "stage_id":stage.id
            }
            lead = request.env["crm.lead"].sudo().create(lead_vals) 
            form_vals = {
                "bs_amount_to_borrow": loan_info.get("amountToBorrow"),
                "bs_monthly_turnover": loan_info.get("monthlyTurnover"),
                "bs_trading_duration": loan_info.get("tradingDuration"),

                "bs_business_name": business.get("businessName"),

                "bs_first_name": applicant.get("firstName"),
                "bs_last_name": applicant.get("lastName"),
                "bs_email": applicant.get("email"),
                "bs_home_owner": applicant.get("homeOwner"),

                "bs_accept_terms": consent.get("acceptedTerms"),

                "lead_agent_notes": payload.get("notes"),
            }
            lead.sudo().write(form_vals)
            return {"status": "success", "lead_id": lead.id, "message": "Business Loan website lead created"}



  
