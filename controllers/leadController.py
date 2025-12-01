# controllers.py
import logging
from odoo import http
from odoo.http import request
import json
import re
from werkzeug.exceptions import BadRequest
from odoo.http import Response



_logger = logging.getLogger(__name__)

class WebsiteLeadsController(http.Controller):
    ROUTE = "/api/website-leads"

    @http.route(ROUTE, type="json", auth="public", methods=["POST"], csrf=False)
    def receive_website_lead(self, **kwargs):
        _logger.info("**********Website Lead API HIT**********")

        api_key = request.httprequest.headers.get("x-api-key")
        if not api_key:
            return {
                "status": "error",
                "message": "Missing header: x-api-key"
            }

        # ---- (Optional) Validate the Key ----
        expected_key = "mysecretkey"
        if api_key != expected_key:
            return {
                "status": "error",
                "message": "Invalid API Key"
            }

        data = json.loads(request.httprequest.data.decode())


        service = data.get("service")
        

        # Dispatch to handlers
        handler_map = {
            "credit_card_website": self._handle_credit_card_website,
            "energy_website": self._handle_energy_website,
            "optus_nbn_website": self._handle_optus_nbn_website,
            "home_moving":self._handle_home_moving,
            "business_loan":self._handle_business_loan,
            "home_loan":self._handle_home_loan,
            "insurance":self._handle_insurance,
            "veu":self._handle_veu
        }

        handler = handler_map.get(service)
        if not handler:
            return {"status": "error", "message": f"No handler for service: {service}"}

        return handler(data)

    # --- Handlers --- #

    def _handle_credit_card_website(self, payload):

        PREFIX_ALLOWED = ["n/a", "mr", "mrs", "ms", "dr", "miss"]
        ANNUAL_REVENUE_ALLOWED = [
            "under_2m", "2m_10m", "10m_50m", "50m_100m", "100m_above"
        ]
        ANNUAL_SPEND_ALLOWED = [
            "under_1m", "2m_5m", "6m_10m", "11m_15m", "16m_20m", "20m_above"
        ]
        CONTACT_METHOD_ALLOWED = ["phone", "email"]
        CONTACT_PREFERENCE_ALLOWED = ["me_first", "referred_first"]


        customer = payload.get("customer", {})
        revenue = payload.get("revenue", {})
        consents = payload.get("consents", {})

        errors = []

        # Helper for checking selection
        def validate_choice(field_name, value, allowed):
            if value and value not in allowed:
                errors.append(
                    f"Invalid value for '{field_name}'. Allowed values are: {', '.join(allowed)}"
                )

        # -------------------------
        # REQUIRED FIELD VALIDATIONS
        # -------------------------
        # required_customer_fields = ["firstName", "lastName", "phone", "email"]
        # for field in required_customer_fields:
        #     if not customer.get(field):
        #         errors.append(f"Missing required field: customer.{field}")


        phone = customer.get("phone")
        email = customer.get("email")

        if phone and not re.match(r"^[0-9+\- ]+$", phone):
            errors.append("Invalid phone number format.")

        if email and "@" not in email:
            errors.append("Invalid email format.")

        # -------------------------
        # Selection Validations
        # -------------------------
        validate_choice("prefix", customer.get("prefix"), PREFIX_ALLOWED)
        validate_choice("annualRevenue", revenue.get("annualRevenue"), ANNUAL_REVENUE_ALLOWED)
        validate_choice("annualSpend", revenue.get("annualSpend"), ANNUAL_SPEND_ALLOWED)
        validate_choice("contactMethod", consents.get("contactMethod"), CONTACT_METHOD_ALLOWED)
        validate_choice("contactPreference", consents.get("contactPreference"), CONTACT_PREFERENCE_ALLOWED)

        # Boolean validation for consent_personal_info
        if consents.get("personalInfo") not in [True, False, None]:
            errors.append("Invalid value for personalInfo. Allowed values: true, false")

        # -------------------------
        # If errors → RETURN
        # -------------------------
        if errors:
            raise BadRequest(json.dumps({
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }))

        # -------------------------
        # Stage Lookup
        # -------------------------
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            raise BadRequest(json.dumps({
                "status": "error",
                "message": "Stage 'Lead Assigned' not found"
            }))

        # -------------------------
        # Create Lead
        # -------------------------
        lead_vals = {
            "name": f"{customer.get('firstName')} {customer.get('lastName')}".strip(),
            "contact_name": f"{customer.get('firstName')} {customer.get('lastName')}".strip(),
            "phone": customer.get("phone"),
            "email_from": customer.get("email"),
            "services": "credit_card_website",
            "lead_for": "credit_card_website",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id,
        }

        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------------------------
        # Write Form Values
        # -------------------------
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
            "username":payload.get("username"),
            "lead_agent_notes": payload.get("notes"),
        }

        lead.sudo().write(form_vals)
        lead.sudo().write({"lead_stage": "2"})

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Credit card website lead created successfully",
        }

    def _validate_energy_payload(self, payload):
        ALLOWED_CONCESSIONS = ["PCC", "HCC", "VCC", "DVA Gold Card", "others"]
        errors = []

        # -------- CUSTOMER --------
        customer = payload.get("customer", {})
        if not customer.get("name"):
            errors.append("name is required.")
        if not customer.get("contactNumber"):
            errors.append("contactNumber is required.")
        if not customer.get("email"):
            errors.append("email is required.")
        if customer.get("email") and "@" not in customer.get("email"):
            errors.append("email is invalid.")

        # -------- PROPERTY --------
        prop = payload.get("property", {})
        if prop.get("propertyType") not in ("residential", "business"):
            errors.append("propertyType must be 'residential' or 'business'.")

        if prop.get("whatToCompare") not in ("electricity_gas", "electricity"):
            errors.append("whatToCompare must be 'electricity_gas' or 'electricity'.")
        
        if prop.get("propertyOwnership") not in ("own", "rent"):
            errors.append("propertyOwnership must be 'own' or 'rent'.")    

        if prop.get("movingIn") not in ("yes", "no"):
            errors.append("movingIn must be yes/no.")

        # -------- PROVIDERS --------
        providers = payload.get("currentProviders", {})

        allowed_providers = [
            "1st_energy", "actew_agl", "agl", "alinta_energy", "aus_power_gas",
            "blue_nrg", "click_energy", "dodo_energy", "energy_australia", "lumo_energy",
            "momentum_energy", "neighbourhood", "online_pow_gas", "origin", "people_energy",
            "power_direct", "powershop", "q_energy", "red_energy", "simple_energy",
            "sumo_power", "tango_energy", "other"
        ]

        allowed_providers_str = ", ".join(allowed_providers)  # for readable messages

        # Electricity Provider Validation
        if providers.get("electricityProvider") and providers["electricityProvider"] not in allowed_providers:
            errors.append(
                f"Invalid electricityProvider. Allowed values are: {allowed_providers_str}"
            )

        # Gas Provider Validation
        if providers.get("gasProvider") and providers["gasProvider"] not in allowed_providers:
            errors.append(
                f"Invalid gasProvider. Allowed values are: {allowed_providers_str}"
            )


        # -------- SERVICE REQUIREMENTS --------
        svc = payload.get("serviceRequirements", {})
        if svc.get("rooftopSolar") not in ("yes", "no", None):
            errors.append("rooftopSolar must be yes/no.")

        if svc.get("requireLifeSupport") not in ("yes", "no", None):
            errors.append("requireLifeSupport must be yes/no.")

        if svc.get("concessionCardHolder") not in ("yes", "no", None):
            errors.append("concessionCardHolder must be yes/no.")

        type_of_concession = svc.get("typeOfConcession") 
        if type_of_concession and type_of_concession not in ALLOWED_CONCESSIONS:
            errors.append(
                f"Invalid typeOfConcession '{type_of_concession}'. Allowed values are: {', '.join(ALLOWED_CONCESSIONS)}"
            ) 

        # -------- USAGE --------
        usage = payload.get("usageInformation", {})
        if usage.get("usageProfile") not in ("low", "medium", "high"):
            errors.append("Invalid usageProfile (low/medium/high).")


        # -------- CONSENTS --------
        consents = payload.get("preferencesAndConsents", {})
        if consents.get("requestCallback") not in ("yes", "no", None):
            errors.append("requestCallback must be yes/no.")

        if consents.get("acceptingTerms") not in (True, False, None):
            errors.append("acceptingTerms must be boolean.")

        return errors
    

    def _handle_energy_website(self, payload):
        # -------- 1. VALIDATE PAYLOAD --------
        errors = self._validate_energy_payload(payload)
        if errors:
            return {
                "status": "error",
                "message": "Validation failed",
                "errors": errors,
            }

        # -------- 2. GET REQUIRED STAGE --------
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        customer = payload.get("customer", {})
        property = payload.get("property", {})
        currentProviders = payload.get("currentProviders", {})
        serviceRequirements = payload.get("serviceRequirements", {})
        usageInformation = payload.get("usageInformation", {})
        preferencesAndConsents = payload.get("preferencesAndConsents", {})

        # -------- 3. CREATE LEAD IN STAGE 1 FIRST --------
        lead_vals = {
            "name": (
                f"{customer.get('name','').strip()}"
                or "Electricity and Gas Lead"
            ),
            "phone": customer.get("phone"),
            "email_from": customer.get("email"),
            "services": "energy_website",
            "lead_for": "energy_website",
            "lead_stage": "1",  # Changed to Stage 1
            "unlock_stage_1": False,
            "stage_id": stage.id,
        }

        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------- 4. WRITE EXTENDED FORM VALUES --------
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
            "username": payload.get("username"),
        }

        lead.sudo().write(form_vals)
        
        # -------- 5. NOW MOVE TO STAGE 2 --------
        lead.sudo().write({"lead_stage": "2"})

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Energy website lead created",
        }




    def _handle_optus_nbn_website(self, payload):


        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        address = payload.get("address", {})
        preferences = payload.get("preferences", {})
        usage = payload.get("usageDetails", {})
        contact = payload.get("contact", {})
        agreement = payload.get("agreement", {})

        errors = []

        # -------------------------
        # Required Fields Validation
        # -------------------------
        # required_contact_fields = ["firstName", "lastName", "phone", "email"]
        # for field in required_contact_fields:
        #     if not contact.get(field):
        #         errors.append(f"Missing required field: contact.{field}")

        if contact.get("phone") and not re.match(r"^[0-9+\- ]+$", contact["phone"]):
            errors.append("Invalid phone number format.")

        if contact.get("email") and "@" not in contact.get("email"):
            errors.append("Invalid email format.")

        if not address.get("currentAddress"):
            errors.append("Missing required field: address.currentAddress")

        # -------------------------
        # Selection Fields Validation
        # -------------------------
        def validate_choice(field_name, value, allowed):
            if value and value not in allowed:
                errors.append(
                    f"Invalid value for '{field_name}': '{value}'. Allowed values are: {', '.join(allowed)}"
                )

        validate_choice(
            "in_important_feature",
            preferences.get("importantFeature"),
            ["speed", "price", "reliability"]
        )
        validate_choice(
            "in_speed_preference",
            preferences.get("speedPreference"),
            ["25Mb", "50Mb", "100Mb", "not_sure"]
        )
        validate_choice(
            "in_broadband_reason",
            preferences.get("broadbandReason"),
            ["moving", "better_plan", "connection"]
        )
        validate_choice(
            "in_when_to_connect_type",
            preferences.get("whenToConnectType"),
            ["asap", "dont_mind", "specific_date"]
        )
        validate_choice(
            "in_internet_users_count",
            usage.get("internetUsersCount"),
            ["1", "2", "3", "4", "5+"]
        )
        validate_choice(
            "in_internet_usage_type",
            usage.get("internetUsageType"),
            ["browsing_email", "work", "social_media", "gaming", "streaming"]
        )
        validate_choice(
            "in_compare_plans",
            usage.get("comparePlans"),
            ["yes", "no"]
        )

        # Boolean Validation
        if agreement.get("acceptTerms") not in [True, False]:
            errors.append("Invalid value for agreement.acceptTerms. Allowed: true, false")

        # -------------------------
        # Return errors if any
        # -------------------------
        if errors:
            return {
                "status": "error",
                "message": "Validation failed",
                "errors": errors,
            }

        # -------------------------
        # Create Lead
        # -------------------------
        lead_vals = {
            "name": f"{contact.get('firstName','')} {contact.get('lastName','')}".strip() or "Optus NBN Lead",
            "contact_name": f"{contact.get('firstName','')} {contact.get('lastName','')}".strip(),
            "phone": contact.get("phone"),
            "email_from": contact.get("email"),
            "services": "optus_nbn_website",
            "lead_for": "optus_nbn_website",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id,
        }

        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------------------------
        # Write Form Values
        # -------------------------
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
            "in_name": contact.get("firstName") + " " + contact.get("lastName"),
            "in_contact_number": contact.get("phone"),
            "in_email": contact.get("email"),
            "in_accept_terms": agreement.get("acceptTerms"),
            "lead_agent_notes": payload.get("notes"),
        }

        lead.sudo().write(form_vals)
        lead.sudo().write({"lead_stage": "2"})

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Optus NBN website lead created successfully"
        }


    def _handle_home_moving(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        moving = payload.get("movingInformation", {})
        propertyContact = payload.get("propertyContact", {})
        personal = payload.get("personalInformation", {})
        contact = payload.get("contactInformation", {})
        referral = payload.get("referralMarketing", {})
        services = payload.get("servicesToConnect", {})

        errors = []

        # -------------------------
        # REQUIRED FIELD VALIDATIONS
        # -------------------------
        # if not moving.get("movingDate"):
        #     errors.append("Missing required field: movingInformation.movingDate")
        # if not moving.get("address"):
        #     errors.append("Missing required field: movingInformation.address")
        # if not personal.get("firstName") or not personal.get("lastName"):
        #     errors.append("Missing required fields: personalInformation.firstName / lastName")
        # if not contact.get("mobile") and not contact.get("homePhone") and not contact.get("workPhone"):
        #     errors.append("At least one contact number is required")
        # if not contact.get("email"):
        #     errors.append("Missing required field: contactInformation.email")

        # -------------------------
        # SELECTION VALIDATIONS
        # -------------------------
        PROPERTY_TYPE_ALLOWED = ["business", "residential"]
        OWNERSHIP_ALLOWED = ["own", "rent"]
        STATUS_ALLOWED = ["n/a", "dr", "mr", "mrs", "ms", "miss"]
        HOW_HEARD_ALLOWED = ["google", "facebook", "word_of_mouth", "real_estate", "other"]

        def validate_choice(field_name, value, allowed):
            if value and value not in allowed:
                errors.append(f"Invalid value for '{field_name}'. Allowed values: {', '.join(allowed)}")

        validate_choice("hm_property_type", moving.get("propertyType"), PROPERTY_TYPE_ALLOWED)
        validate_choice("hm_ownership", moving.get("ownership"), OWNERSHIP_ALLOWED)
        validate_choice("hm_status", personal.get("status"), STATUS_ALLOWED)
        validate_choice("hm_how_heard", referral.get("howHeard"), HOW_HEARD_ALLOWED)

        # -------------------------
        # BOOLEAN VALIDATIONS
        # -------------------------
        for svc_field in [
            "electricity", "gas", "internet", "water", "tv", "removalist"
        ]:
            val = services.get(svc_field)
            if val not in [True, False, None]:
                errors.append(f"Invalid value for servicesToConnect.{svc_field}. Allowed: true, false")

        if errors:
            return {
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }

        # -------------------------
        # CREATE LEAD
        # -------------------------
        lead_vals = {
            "name": f"{personal.get('firstName', '').strip()} {personal.get('lastName', '').strip()}" or "Home Moving Lead",
            "contact_name": f"{contact.get('firstName','')} {contact.get('lastName','')}".strip() or "",
            "phone": contact.get("mobile"),
            "email_from": contact.get("email"),
            "services": "home_moving",
            "lead_for": "home_moving",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------------------------
        # WRITE FORM VALUES
        # -------------------------
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
            "hm_accept_terms": payload.get("acceptTerms"),
        }

        lead.sudo().write(form_vals)
        lead.sudo().write({"lead_stage": "2"})

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Home Moving website lead created"
        }




    def _handle_business_loan(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        loan_info = payload.get("loanInformation", {})
        business = payload.get("businessDetails", {})
        applicant = payload.get("applicantInformation", {})
        consent = payload.get("consent", {})

        errors = []

        # -------------------------
        # REQUIRED FIELDS
        # -------------------------
        # if not applicant.get("firstName") or not applicant.get("lastName"):
        #     errors.append("Missing required fields: applicantInformation.firstName / lastName")
        # if not applicant.get("email"):
        #     errors.append("Missing required field: applicantInformation.email")
        # if not applicant.get("mobile"):
        #     errors.append("Missing required field: applicantInformation.mobile")
        # if not loan_info.get("amountToBorrow"):
        #     errors.append("Missing required field: loanInformation.amountToBorrow")
        # if not consent.get("acceptedTerms"):
        #     errors.append("You must accept terms and conditions")

        # -------------------------
        # SELECTION VALIDATIONS
        # -------------------------
        AMOUNT_ALLOWED = ["under_50k","50k_100k","100k_150k","200k_300k","300k_500k","above_500k"]
        DURATION_ALLOWED = ["0-6 months","6-12 months","12-24 months","over 24 months"]

        if loan_info.get("amountToBorrow") not in AMOUNT_ALLOWED:
            errors.append(f"Invalid amountToBorrow. Allowed values: {', '.join(AMOUNT_ALLOWED)}")
        if loan_info.get("tradingDuration") not in DURATION_ALLOWED:
            errors.append(f"Invalid tradingDuration. Allowed values: {', '.join(DURATION_ALLOWED)}")

        if errors:
            return {
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }

        # -------------------------
        # CREATE LEAD
        # -------------------------
        lead_vals = {
            "name": f"{applicant.get('firstName', '').strip()} {applicant.get('lastName', '').strip()}" or "Business Loan Lead",
            "contact_name": f"{applicant.get('firstName','')} {applicant.get('lastName','')}".strip() or "",
            "phone": applicant.get("mobile"),
            "email_from": applicant.get("email"),
            "services": "business_loan",
            "lead_for": "business_loan",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------------------------
        # WRITE FORM VALUES
        # -------------------------
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
        lead.sudo().write({"lead_stage": "2"})

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Business Loan website lead created"
        }


    def _handle_home_loan(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        loan_intent = payload.get("loanIntent", {})
        property_details = payload.get("propertyDetails", {})
        financial = payload.get("financialBackground", {})
        applicant = payload.get("applicantInformation", {})
        consent = payload.get("acceptedTerms", {})

        errors = []

        # -------------------------
        # REQUIRED FIELDS
        # -------------------------
        # if not applicant.get("firstName") or not applicant.get("lastName"):
        #     errors.append("Missing required fields: applicantInformation.firstName / lastName")
        # if not applicant.get("email"):
        #     errors.append("Missing required field: applicantInformation.email")
        # if not applicant.get("mobile"):
        #     errors.append("Missing required field: applicantInformation.mobile")
        # if not loan_intent.get("userWantTo"):
        #     errors.append("Missing required field: loanIntent.userWantTo")
        # if not property_details.get("propertyType"):
        #     errors.append("Missing required field: propertyDetails.propertyType")
        # if not consent.get("acceptedTerms"):
        #     errors.append("You must accept terms and conditions")

        # -------------------------
        # SELECTION VALIDATIONS
        # -------------------------
        USER_WANT_TO_ALLOWED = ["refinance", "buy_home"]
        BUYING_REASON_ALLOWED = ["just_exploring", "planning_to_buy", "actively_looking", "exchanged_contracts"]
        PROPERTY_TYPE_ALLOWED = ["established_home", "newly_built", "vacant_land"]
        PROPERTY_USAGE_ALLOWED = ["to_live", "for_investment"]
        CREDIT_HISTORY_ALLOWED = ["excellent", "average", "fair", "don't know"]
        INCOME_SOURCE_ALLOWED = ["employee", "business", "other"]

        if loan_intent.get("userWantTo") not in USER_WANT_TO_ALLOWED:
            errors.append(f"Invalid userWantTo. Allowed values: {', '.join(USER_WANT_TO_ALLOWED)}")
        if loan_intent.get("buyingReason") and loan_intent.get("buyingReason") not in BUYING_REASON_ALLOWED:
            errors.append(f"Invalid buyingReason. Allowed values: {', '.join(BUYING_REASON_ALLOWED)}")
        if property_details.get("propertyType") and property_details.get("propertyType") not in PROPERTY_TYPE_ALLOWED:
            errors.append(f"Invalid propertyType. Allowed values: {', '.join(PROPERTY_TYPE_ALLOWED)}")
        if property_details.get("propertyUsage") and property_details.get("propertyUsage") not in PROPERTY_USAGE_ALLOWED:
            errors.append(f"Invalid propertyUsage. Allowed values: {', '.join(PROPERTY_USAGE_ALLOWED)}")
        if financial.get("creditHistory") and financial.get("creditHistory") not in CREDIT_HISTORY_ALLOWED:
            errors.append(f"Invalid creditHistory. Allowed values: {', '.join(CREDIT_HISTORY_ALLOWED)}")
        if financial.get("incomeSource") and financial.get("incomeSource") not in INCOME_SOURCE_ALLOWED:
            errors.append(f"Invalid incomeSource. Allowed values: {', '.join(INCOME_SOURCE_ALLOWED)}")

        # -------------------------
        # RETURN ERRORS IF ANY
        # -------------------------
        if errors:
            return {
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }

        # -------------------------
        # CREATE LEAD
        # -------------------------
        lead_vals = {
            "name": f"{applicant.get('firstName', '').strip()} {applicant.get('lastName', '').strip()}" or "Home Loan Lead",
            "contact_name": f"{applicant.get('firstName','')} {applicant.get('lastName','')}".strip() or "",
            "phone": applicant.get("mobile"),
            "email_from": applicant.get("email"),
            "services": "home_loan",
            "lead_for": "home_loan",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)
        

        # -------------------------
        # WRITE FORM VALUES
        # -------------------------
        form_vals = {
            "hl_user_want_to": loan_intent.get("userWantTo"),
            "hl_buying_reason": loan_intent.get("buyingReason"),
            "hl_first_home_buyer": loan_intent.get("firstHomeBuyer"),
            "hl_property_type": property_details.get("propertyType"),
            "hl_property_usage": property_details.get("propertyUsage"),
            "hl_expected_price": property_details.get("expectedPrice"),
            "hl_deposit_amount": property_details.get("depositAmount"),
            "hl_credit_history": financial.get("creditHistory"),
            "hl_income_source": financial.get("incomeSource"),
            "hl_first_name": applicant.get("firstName"),
            "hl_last_name": applicant.get("lastName"),
            "hl_contact": applicant.get("mobile"),
            "hl_email": applicant.get("email"),
            "hl_accept_terms": consent.get("acceptedTerms"),
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(form_vals)
        lead.sudo().write({"lead_stage": "2"})

        return {
            "status": "success",
            "lead_id": lead.id,
            "message": "Home Loan website lead created"
        }



    def _handle_insurance(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        insurance_details = payload.get("insuranceDetails", {})
        personal_info = payload.get("personalInformation", {})
        address = payload.get("address", {})
        financial_info = payload.get("financialInformation", {})

        errors = []

        # -------------------------
        # REQUIRED FIELDS
        # -------------------------
        # if not personal_info.get("fullName"):
        #     errors.append("Missing required field: personalInformation.fullName")
        # if not personal_info.get("dob"):
        #     errors.append("Missing required field: personalInformation.dob")
        # if not personal_info.get("contactNumber"):
        #     errors.append("Missing required field: personalInformation.contactNumber")
        # if not personal_info.get("email"):
        #     errors.append("Missing required field: personalInformation.email")
        # if not address.get("currentAddress"):
        #     errors.append("Missing required field: address.currentAddress")
        # if not insurance_details.get("coverType"):
        #     errors.append("Missing required field: insuranceDetails.coverType")
        # if not insurance_details.get("haveInsuranceCover"):
        #     errors.append("Missing required field: insuranceDetails.haveInsuranceCover")
        # if not insurance_details.get("insuranceConsiderations"):
        #     errors.append("Missing required field: insuranceDetails.insuranceConsiderations")
        # if not financial_info.get("annualTaxableIncome"):
        #     errors.append("Missing required field: financialInformation.annualTaxableIncome")

        # -------------------------
        # SELECTION VALIDATIONS
        # -------------------------
        COVER_TYPE_ALLOWED = ["hospital_extras", "hospital", "extras"]
        YES_NO_ALLOWED = ["yes", "no"]
        CONSIDERATIONS_ALLOWED = [
            "health_concern", "save_money", "no_insurance_before", "better_health_cover",
            "need_for_tax", "planning_a_baby", "changed_circumstances", "compare_options"
        ]
        INCOME_ALLOWED = ["$97,000_or_less", "$97,001_$113,000", "$113,001_$151,000", "$151,001_or_more"]

        if insurance_details.get("coverType") and insurance_details.get("coverType") not in COVER_TYPE_ALLOWED:
            errors.append(f"Invalid coverType. Allowed values: {', '.join(COVER_TYPE_ALLOWED)}")
        if insurance_details.get("haveInsuranceCover") and insurance_details.get("haveInsuranceCover") not in YES_NO_ALLOWED:
            errors.append(f"Invalid haveInsuranceCover. Allowed values: {', '.join(YES_NO_ALLOWED)}")
        if insurance_details.get("insuranceConsiderations") and insurance_details.get("insuranceConsiderations") not in CONSIDERATIONS_ALLOWED:
            errors.append(f"Invalid insuranceConsiderations. Allowed values: {', '.join(CONSIDERATIONS_ALLOWED)}")
        if financial_info.get("annualTaxableIncome") and financial_info.get("annualTaxableIncome") not in INCOME_ALLOWED:
            errors.append(f"Invalid annualTaxableIncome. Allowed values: {', '.join(INCOME_ALLOWED)}")

        # -------------------------
        # RETURN ERRORS IF ANY
        # -------------------------
        if errors:
            return {"status": "error", "message": "Validation failed", "errors": errors}

        # -------------------------
        # CREATE LEAD
        # -------------------------
        lead_vals = {
            "name": personal_info.get("fullName", "Health Insurance Lead"),
            "contact_name": personal_info.get("fullName", ""),
            "phone": personal_info.get("contactNumber"),
            "email_from": personal_info.get("email"),
            "services": "insurance",
            "lead_for": "insurance",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------------------------
        # WRITE FORM VALUES
        # -------------------------
        form_vals = {
            "hi_cover_type": insurance_details.get("coverType"),
            "hi_have_insurance_cover": insurance_details.get("haveInsuranceCover"),
            "hi_insurance_considerations": insurance_details.get("insuranceConsiderations"),
            "hi_full_name": personal_info.get("fullName"),
            "hi_dob": personal_info.get("dob"),
            "hi_contact_number": personal_info.get("contactNumber"),
            "hi_email": personal_info.get("email"),
            "hi_current_address": address.get("currentAddress"),
            "hi_annual_taxable_income": financial_info.get("annualTaxableIncome"),
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(form_vals)
        lead.sudo().write({"lead_stage": "2"})

        return {"status": "success", "lead_id": lead.id, "message": "Health Insurance website lead created"}



    def _handle_veu(self, payload):
        stage = request.env["crm.stage"].sudo().search([("name", "=", "Lead Assigned")], limit=1)
        if not stage:
            return {"status": "error", "message": "Stage 'Lead Assigned' not found"}

        applicant_info = payload.get("applicantInformation", {})
        rebate_info = payload.get("rebateInformation", {})
        consent = payload.get("acceptedTerms", {})

        errors = []

        # -------------------------
        # REQUIRED FIELDS
        # -------------------------
        # if not applicant_info.get("firstName"):
        #     errors.append("Missing required field: applicantInformation.firstName")
        # if not applicant_info.get("lastName"):
        #     errors.append("Missing required field: applicantInformation.lastName")
        # if not applicant_info.get("mobileNo"):
        #     errors.append("Missing required field: applicantInformation.mobileNo")
        # if not applicant_info.get("email"):
        #     errors.append("Missing required field: applicantInformation.email")
        # if not applicant_info.get("postCode"):
        #     errors.append("Missing required field: applicantInformation.postCode")
        # if not rebate_info.get("interestedIn"):
        #     errors.append("Missing required field: rebateInformation.interestedIn")
        # if not rebate_info.get("how"):
        #     errors.append("Missing required field: rebateInformation.how")
        # if not consent.get("acceptTerms"):
        #     errors.append("You must accept the terms and conditions")

        # -------------------------
        # SELECTION VALIDATION
        # -------------------------
        INTEREST_ALLOWED = ["air", "water_res", "water_com"]
        if rebate_info.get("interestedIn") and rebate_info.get("interestedIn") not in INTEREST_ALLOWED:
            errors.append(f"Invalid interestedIn value. Allowed: {', '.join(INTEREST_ALLOWED)}")

        # -------------------------
        # RETURN ERRORS IF ANY
        # -------------------------
        if errors:
            return {"status": "error", "message": "Validation failed", "errors": errors}

        # -------------------------
        # CREATE LEAD
        # -------------------------
        lead_vals = {
            "name": (
                f"{applicant_info.get('firstName', '').strip()} {applicant_info.get('lastName', '').strip()}"
                or applicant_info.get("name", "Victorian Energy Upgrade Lead")
            ),
            "contact_name": f"{applicant_info.get('firstName','')} {applicant_info.get('lastName','')}".strip() or "",
            "phone": applicant_info.get("mobileNo"),
            "email_from": applicant_info.get("email"),
            "services": "veu",
            "lead_for": "veu",
            "lead_stage": "1",
            "unlock_stage_1": False,
            "stage_id": stage.id
        }
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        # -------------------------
        # WRITE FORM VALUES
        # -------------------------
        form_vals = {
            "u_first_name": applicant_info.get("firstName"),
            "u_last_name": applicant_info.get("lastName"),
            "u_mobile_no": applicant_info.get("mobileNo"),
            "u_email": applicant_info.get("email"),
            "u_post_code": applicant_info.get("postCode"),
            "u_interested_in": rebate_info.get("interestedIn"),
            "u_how": rebate_info.get("how"),
            "u_accept_terms": consent.get("acceptTerms"),
            "lead_agent_notes": payload.get("notes"),
        }
        lead.sudo().write(form_vals)
        lead.sudo().write({"lead_stage": "2"})

        return {"status": "success", "lead_id": lead.id, "message": "Victorian Energy Upgrade Website lead created"}





      

 


  
