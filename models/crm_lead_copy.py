from odoo import models, fields, api
import logging
import json

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    external_api_id = fields.Integer("External API ID", index=True)
    vicidial_lead_id = fields.Integer("Vicidial Lead Id")
    partner_latitude = fields.Float(
        string='Latitude',
        related='partner_id.partner_latitude',
        store=True
    )

    partner_longitude = fields.Float(
        string='Longitude',
        related='partner_id.partner_longitude',
        store=True
    )

    # Example: Custom field for automatic assignment logic
    assignation_id = fields.Many2one(
        'res.partner',
        string='Automatically Assigned Partner'
    )

    services = fields.Selection([
        ('credit_card', 'Credit Card AMEX'),
        ('energy', 'Electricity & Gas'),
        ('optus_nbn', 'Optus NBN Form'),
    ],  required=True)

    @api.model
    def _get_stage_sequence(self):
        """Return the ordered stages for the wizard navigation."""
        return ["1", "2", "3"]  # your lead_stage values

    def action_prev_stage(self):
        """Move to previous stage"""
        _logger.info("Previous button clicked for lead IDs: %s", self.ids)

        result = {}
        for lead in self:
            current_stage = int(lead.lead_stage or "1")

            if current_stage <= 1:
                _logger.warning("Lead %s already at minimum stage", lead.id)
                result = {"success": False, "error": "Already at first stage"}
            else:
                new_stage = str(current_stage - 1)
                lead.with_context(skip_stage_assign=True).write({"lead_stage": new_stage})
                _logger.info("Lead %s moved from stage %s to %s", lead.id, current_stage, new_stage)
                result = {"success": True, "new_stage": new_stage}

        return result


    def action_next_stage(self):
        _logger.info("self is %s ", self)
        """Move to next stage"""
        _logger.info("Next button clicked for lead IDs: %s", self.ids)

        result = {}
        for lead in self:
            _logger.info("Lead current state is %s", lead.lead_stage)
            current_stage = int(lead.lead_stage or "1")

            if current_stage >= 3:
                _logger.warning("Lead %s already at maximum stage", lead.id)
                result = {"success": False, "error": "Already at last stage"}
                continue
  
            # Stage 1 → Stage 2
            if current_stage == 1:
                if lead.en_name or lead.en_contact_number or lead.cc_prefix or lead.cc_first_name:
                    new_stage = "2"
                    lead.with_context(skip_stage_assign=True).write({"lead_stage": new_stage})
                    _logger.info("Lead current state after writing is %s", lead.lead_stage)

                    _logger.info("Lead %s moved 1 → 2", lead.id)
                    result = {"success": True, "new_stage": new_stage}
                else:
                    result = {"success": False, "error": "Please fill required fields before moving to stage 2"}

            # Stage 2 → Stage 3
            elif current_stage == 2:
                if lead.disposition == "sold_pending_quality":
                    new_stage = "3"
                    _logger.info("Lead current state after stage 2 wroting is %s", lead.lead_stage)

                    lead.with_context(skip_stage_assign=True).write({"lead_stage": new_stage})
                    _logger.info("Lead %s moved 2 → 3", lead.id)
                    result = {"success": True, "new_stage": new_stage}
                else:
                    result = {"success": False, "error": "Please set disposition before moving to stage 3"}

        return result





    @api.depends('services')
    def _compute_lead_for(self):
        for record in self:
            if record.services:
                record.lead_for = record.services
            else:
                record.lead_for = False
            


    # Core fields that trigger stage computation
    customer_name = fields.Char(string="Customer Name")
    customer_mobile_number = fields.Char(string="Customer Mobile Number")
    lead_for = fields.Char(
    string="Lead for", 
    readonly=True, 
    compute="_compute_lead_for",
    store=True
)
    
    # Lead stage field - computed and stored
    lead_stage = fields.Selection([
        ("1", "Stage 1"),
        ("2", "Stage 2"),
        ("3", "Stage 3"),
        ("4", "Stage 4"),
    ], string="Lead Current Stage : ", default="1", store=True, readonly=True)

    en_current_address = fields.Char(string="Current Address")
    en_what_to_compare = fields.Selection([
        ('electricity_gas', 'Electricity & Gas'),
        ('electricity', 'Elecricity'),
    ], string="What are you looking to compare?")
    en_property_type = fields.Selection([
        ('residential', 'Residential'),
        ('business', 'Business'),
    ], string="What type of property?")
    en_moving_in = fields.Boolean(string="Are you moving into this property?")
    en_date = fields.Date("Date")
    en_property_ownership = fields.Selection([
        ('own', 'Own'),
        ('rent', 'Rent'),
    ], string="Do you own or rent this property?")
    en_usage_profile = fields.Selection([
        ('low', '1-2 people, spemd minimal time at home, weekly washing, minimal heating, cooking.'),
        ('medium', '3-4 people, home in the evening and weekend regular washing, heating and cooling.'),
        ('high', '5+ people, home during the day, evenings and weekend daily washing, heating and cooling.')
    ], string="Usage Profile")
    en_require_life_support = fields.Boolean(string="Does anyone residing or intending to reside at your premises require life support equipment?")
    en_concesion_card_holder = fields.Boolean("Are you a concession card holder?")
    en_rooftop_solar = fields.Boolean(string="Do you have rooftop solar panels :")
    en_electricity_provider = fields.Selection([
        ('1st_energy', '1st Energy'),
        ('actew_agl', 'ActewAGL'),
        ('agl', 'AGL'),
        ('alinta_energy', 'Alinta Energy'),
        ('aus_power_gas', 'Australian Power & Gas'),
        ('blue_nrg', 'BlueNRG'),
        ('click_energy', 'Click Energy'),
        ('dodo_energy', 'Dodo Energy'),
        ('energy_australia', 'Energy Australia'),
        ('lumo_energy', 'Lumo Energy'),
        ('momentum_energy', 'Momentum Energy'),
        ('neighbourhood', 'Neighbourhood'),
        ('online_pow_gas', 'Online Power & Gas'),
        ('origin', 'Orgin'),
        ('people_energy', 'People Energy'),
        ('power_direct', 'Power Direct'),
        ('powershop', 'Powershop'),
        ('q_energy', 'QEnergy'),
        ('red_energy', 'Red Energy'),
        ('simple_energy', 'Simple Energy'),
        ('sumo_power', 'Sumo Power'),
        ('tango_energy', 'Tango Energy'),
        ('other', 'Other/Unknown'),

    ],"Who is your current electricity provider")

    en_gas_provider = fields.Selection([
        ('1st_energy', '1st Energy'),
        ('actew_agl', 'ActewAGL'),
        ('agl', 'AGL'),
        ('alinta_energy', 'Alinta Energy'),
        ('aus_power_gas', 'Australian Power & Gas'),
        ('blue_nrg', 'BlueNRG'),
        ('click_energy', 'Click Energy'),
        ('dodo_energy', 'Dodo Energy'),
        ('energy_australia', 'Energy Australia'),
        ('lumo_energy', 'Lumo Energy'),
        ('momentum_energy', 'Momentum Energy'),
        ('neighbourhood', 'Neighbourhood'),
        ('online_pow_gas', 'Online Power & Gas'),
        ('origin', 'Orgin'),
        ('people_energy', 'People Energy'),
        ('power_direct', 'Power Direct'),
        ('powershop', 'Powershop'),
        ('q_energy', 'QEnergy'),
        ('red_energy', 'Red Energy'),
        ('simple_energy', 'Simple Energy'),
        ('sumo_power', 'Sumo Power'),
        ('tango_energy', 'Tango Energy'),
        ('other', 'Other/Unknown'),

    ],"Who is your current gas provider")
    en_name = fields.Char("Name")
    en_contact_number = fields.Char("Contact Number")
    en_customer_alt_phone = fields.Char(string="Customer Alt. Number")
    en_email = fields.Char("Email")
    en_request_callback = fields.Boolean(string="Request a call back")
    en_accpeting_terms = fields.Boolean(string="By submitting your details you agree that you have read and agreed to the Terms and Conditions and Privacy Policy.")
    nmi = fields.Char(string="NMI")
    mirn = fields.Char(string="MIRN")
    frmp = fields.Char(string="FRMP")
    type_of_concession = fields.Selection([
        ("pcc", "PCC"),
        ("hcc","HCC"),
        ("vcc", "VCC"),
        ("others", "Others")
    ], string="Type of Concession", default="pcc")
    lead_agent_notes = fields.Text(string="Notes By Lead Agent")

    # Stage 2 fields
    stage_2_dob = fields.Date(string="Date of Birth")
    stage_2_id_proof_type = fields.Selection([
        ("driver_licence", "Driver Licence"),
        ("medicare_card", "Medicare Card"),
        ("passport", "Passport"),
    ], string="Type Of ID Proof", default="driver_licence")
    stage_2_id_proof_name = fields.Char(string="Name of ID Proof")
    stage_2_id_number = fields.Char(string="ID Number")
    stage_2_id_start_date = fields.Date(string="ID Start Date")
    stage_2_id_expiry_date = fields.Date(string="ID Expire date")
    stage_2_id_issuance_state = fields.Char(string="ID Issuance State")
    stage_2_concession_type = fields.Selection([
        ("pcc", "PCC"),
        ("hcc","HCC"),
        ("vcc", "VCC"),
        ("others", "Others")
    ], string="Type of Concession", default="pcc")
    stage_2_card_number = fields.Char(string="Concession Card Number")
    stage_2_card_holder_name = fields.Char(string="Concession Card Holder Name")
    stage_2_card_type = fields.Char(string="Concession Card Type")
    stage_2_card_start_date = fields.Date(string="Concession Card Start Date")
    stage_2_card_expiry_date = fields.Date(string="Concession Card Expiry Date")
    stage_2_sec_acc_holder = fields.Char(string="Secondary Account Holder Name")
    stage_2_sec_acc_holder_dob = fields.Char(string="Secondary Account Holder DOB")
    stage_2_sec_acc_holder_mobile = fields.Char(string="Secondary Account Holder Mobile")
    stage_2_sec_acc_holder_email = fields.Char(string="Secondary Account Holder Email")
    stage_2_bill = fields.Selection([
        ("postal", "Postal"),
        ("email","Email")
    ], string="Bill", default="postal")
    stage_2_dnc = fields.Char(string="DNC")
    stage_2_lead_agent = fields.Char(string="Lead Agent")
    stage_2_head_transfer_name = fields.Char(string="Head Transfer Name")
    stage_2_closer_name = fields.Char(string="Closer Name")
    stage_2_sale_date = fields.Date(string="Sale Date")
    stage_2_campign_name = fields.Selection([
        ("dodo_power_gas", "DODO Power & Gas"),
        ("first_energy", "1st energy"),
        ("momentum","Momentum")
    ],string="Campign Name", default="dodo_power_gas")
    stage_2_lead_source = fields.Char(string="Lead Source")
    stage_2_lead_agent_notes = fields.Text(string="Notes By Lead Agent")
    disposition = fields.Selection([
    ("callback", "Callback"),
    ("lost", "Lost"),
    ("sold_pending_quality", "Sold – Pending Quality"),
    ], string="Disposition")
    callback_date = fields.Datetime("Callback Date")


    
    # FIRST ENERGY FIELDS
    internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    existing_sale = fields.Char(string="Existing Sale with NMI & Phone Number")
    online_enquiry_form = fields.Char(string="Online Enquiry Form")
    vendor_id = fields.Char(string="Vendor ID", default="Utility Hub")
    agent = fields.Char(string="Agent")
    channel_ref = fields.Char(string="Channel Reference")
    sale_ref = fields.Char(string="Sale Reference")
    lead_ref = fields.Char(string="Lead Ref (External)")  # renamed to avoid clash
    incentive = fields.Char(string="Incentive")
    sale_date = fields.Date(string="Date of Sale")
    campaign_ref = fields.Char(string="Campaign Reference")
    promo_code = fields.Char(string="Promo Code")
    current_elec_retailer = fields.Char(string="Current Electric Retailer")
    current_gas_retailer = fields.Char(string="Current Gas Retailer")
    multisite = fields.Boolean(string="Multisite")
    existing_customer = fields.Boolean(string="Existing Customer")
    customer_account_no = fields.Char(string="Customer Account Number")
    customer_type = fields.Selection([
        ('resident', 'Resident'),
        ('company', 'Company'),
    ], string='Customer Type', default="resident")
    account_name = fields.Char(string="Account Name")
    abn = fields.Char(string="ABN")
    acn = fields.Char(string="ACN")
    business_name = fields.Char(string="Business Name")
    trustee_name = fields.Char(string="Trustee Name")
    trading_name = fields.Char(string="Trading Name")
    position = fields.Char(string="Position")
    sale_type = fields.Selection([
        ('transfer', 'Transfer'),
        ('movein', 'Movein')
    ], string="Sale Type", default="transfer")
    customer_title = fields.Char(string="Title")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    phone_landline = fields.Char(string="Phone Landline")
    phone_mobile = fields.Char(string="Mobile Number")
    auth_date_of_birth = fields.Date(string="Authentication Date of Birth")
    auth_expiry = fields.Date(string="Authentication Expiry")
    auth_no = fields.Char(string="Authentication No")
    auth_type = fields.Char(string="Authentication Type")
    email = fields.Char(string="Email")
    life_support = fields.Boolean(string="Life Support", default=False)
    concessioner_number = fields.Char(string="Concessioner Number")
    concession_expiry = fields.Date(string="Concession Expiry Date")
    concession_flag = fields.Boolean(string="Concession Flag", default=False)
    concession_start_date = fields.Date(string="Concession Start Date")
    concession_type = fields.Char(string="Concession Type")
    conc_first_name = fields.Char(string="Concession First Name")
    conc_last_name = fields.Char(string="Concession Last Name")
    secondary_title = fields.Char(string="Secondary Title")
    sec_first_name = fields.Char(string="Secondary First Name")
    sec_last_name = fields.Char(string="Secondary Last Name")
    sec_auth_date_of_birth = fields.Date(string="Secondary Authentication DOB")
    sec_auth_no = fields.Char(string="Secondary Authentication No")
    sec_auth_type = fields.Char(string="Secondary Authentication Type")
    sec_auth_expiry = fields.Date(string="Secondary Authentication Expiry")
    sec_email = fields.Char(string="Secondary Email")
    sec_phone_home = fields.Char(string="Secondary Phone Home")
    sec_mobile_number = fields.Char(string="Secondary Mobile Number")
    site_apartment_no = fields.Char(string="Site Apartment Number")
    site_apartment_type = fields.Char(string="Site Apartment Type")
    site_building_name = fields.Char(string="Site Building Name")
    site_floor_no = fields.Char(string="Site Floor Number")
    site_floor_type = fields.Char(string="Site Floor Type")
    site_location_description = fields.Text(string="Site Location Description")
    site_lot_number = fields.Char(string="Site Lot Number")
    site_street_number = fields.Char(string="Site Street Number")
    site_street_name = fields.Char(string="Site Street Name")
    site_street_number_suffix = fields.Char(string="Site Street Number Suffix")
    site_street_type = fields.Char(string="Site Street Type")
    site_street_suffix = fields.Char(string="Site Street Suffix")
    site_suburb = fields.Char(string="Site Suburb")
    site_state = fields.Char(string="Site State")
    site_post_code = fields.Char(string="Site Post Code")
    gas_site_apartment_number = fields.Char(string="Gas Site Apartment Number")
    gas_site_apartment_type = fields.Char(string="Gas Site Apartment Type")
    gas_site_building_name = fields.Char(string="Gas Site Building Name")
    gas_site_floor_number = fields.Char(string="Gas Site Floor Number")
    gas_site_floor_type = fields.Char(string="Gas Site Floor Type")
    gas_site_location_description = fields.Char(string="Gas Site Location Description")
    gas_site_lot_number = fields.Char(string="Gas Site Lot Number")
    gas_site_street_name = fields.Char(string="Gas Site Street Name")
    gas_site_street_number = fields.Char(string="Gas Site Street Number")
    gas_site_street_number_suffix = fields.Char(string="Gas Site Street Number Suffix")  # typo fixed
    gas_site_street_type = fields.Char(string="Gas Site Street Type")
    gas_site_street_suffix = fields.Char("Gas Site Street Suffix")
    gas_site_suburb = fields.Char("Gas Site Suburb")
    gas_site_state = fields.Char("Gas Site State")
    gas_site_post_code = fields.Char("Gas Site Post Code")
    network_tariff_code = fields.Char("Network Tariff Code")
    nmi = fields.Char("NMI")
    mirn = fields.Char("MIRN")
    fuel = fields.Char("Fuel")
    feed_in = fields.Char("Feed In")
    annual_usage = fields.Float("Annual Usage")
    gas_annual_usage = fields.Float("Gas Annual Usage")
    product_code = fields.Char("Product Code")
    gas_product_code = fields.Char("Gas Product Code")
    offer_description = fields.Text("Offer Description")
    gas_offer_description = fields.Text("Gas Offer Description")
    green_percent = fields.Float("Green Percent")
    proposed_transfer_date = fields.Date("Proposed Transfer Date")
    gas_proposed_transfer_date = fields.Date("Gas Proposed Transfer Date")
    bill_cycle_code = fields.Char("Bill Cycle Code")
    gas_bill_cycle_code = fields.Char("Gas Bill Cycle Code")
    average_monthly_spend = fields.Float("Average Monthly Spend")
    is_owner = fields.Boolean("Is Owner")
    has_accepted_marketing = fields.Boolean("Has Accepted Marketing")
    email_account_notice = fields.Boolean("Email Account Notice")
    email_invoice = fields.Boolean("Email Invoice")
    billing_email = fields.Char("Billing Email")
    postal_building_name = fields.Char("Postal Building Name")
    postal_apartment_number = fields.Char("Postal Apartment Number")
    postal_apartment_type = fields.Char("Postal Apartment Type")
    postal_floor_number = fields.Char("Postal Floor Number")
    postal_floor_type = fields.Char("Postal Floor Type")
    postal_lot_no = fields.Char("Postal Lot No")
    postal_street_number = fields.Char("Postal Street Number")
    postal_street_number_suffix = fields.Char("Postal Street Number Suffix")
    postal_street_name = fields.Char("Postal Street Name")
    postal_street_type = fields.Char("Postal Street Type")
    postal_street_suffix = fields.Char("Postal Street Suffix")
    postal_suburb = fields.Char("Postal Suburb")
    postal_post_code = fields.Char("Postal Post Code")
    postal_state = fields.Char("Postal State")
    comments = fields.Text("Comments")
    transfer_special_instructions = fields.Text("Transfer Special Instructions")
    medical_cooling = fields.Boolean("Medical Cooling")
    medical_cooling_energy_rebate = fields.Boolean("Medical Cooling Energy Rebate")
    benefit_end_date = fields.Date("Benefit End Date")
    sales_class = fields.Char("Sales Class")
    bill_group_code = fields.Char("Bill Group Code")
    gas_meter_number = fields.Char("Gas Meter Number")
    centre_name = fields.Char("Centre Name")
    qc_name = fields.Char("QC Name")
    verifiers_name = fields.Char("Verifier’s Name")
    tl_name = fields.Char("TL Name")
    dnc_ref_no = fields.Char("DNC Ref No")
    audit_2 = fields.Char("Audit-2")
    welcome_call = fields.Boolean("Welcome Call")
    stage_3_dispostion = fields.Selection([
    ("closed", "Sale Closed"),
    ("on_hold", "Hold"),
    ("failed", "Failed"),
    ], string="Disposition by QA Team")
    qa_notes = fields.Char("Notes by QA")

    # DODO POWER AND GAS
    dp_internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    dp_existing_sale = fields.Char(string="Existing Sale with NMI & Phone Number (Internal)")
    dp_online_enquiry_form = fields.Char(string="Online Enquiry Form")
    dp_sales_name = fields.Char(string="Sales Name")
    dp_sales_reference = fields.Char(string="Sales Reference")
    dp_agreement_date = fields.Date(string="Agreement Date")
    dp_site_address_postcode = fields.Char(string="Site Address Postcode")
    dp_site_addr_unit_type = fields.Char(string="Site Addr Unit Type")
    dp_site_addr_unit_no = fields.Char(string="Site Addr Unit No")
    dp_site_addr_floor_type = fields.Char(string="Site Addr Floor Type")
    dp_site_addr_floor_no = fields.Char(string="Site Addr Floor No")
    dp_site_addr_street_no = fields.Char(string="Site Addr Street No")
    dp_site_addr_street_no_suffix = fields.Char(string="Site Addr Street No Suffix")
    dp_site_addr_street_name = fields.Char(string="Site Addr Street Name")
    dp_site_addr_street_type = fields.Char(string="Site Addr Street Type")
    dp_site_addr_suburb = fields.Char(string="Site Addr Suburb")
    dp_site_addr_state = fields.Char(string="Site Addr State")
    dp_site_addr_postcode = fields.Char(string="Site Addr Postcode")
    dp_site_addr_desc = fields.Text(string="Site Address Description")
    dp_site_access = fields.Text(string="Site Access")
    dp_site_more_than_12_months = fields.Boolean(string="At Site > 12 Months")
    dp_prev_addr_1 = fields.Char(string="Previous Address Line 1")
    dp_prev_addr_2 = fields.Char(string="Previous Address Line 2")
    dp_prev_addr_state = fields.Char(string="Previous Address State")
    dp_prev_addr_postcode = fields.Char(string="Previous Address Postcode")
    dp_billing_address = fields.Boolean(string="Billing Address")
    dp_bill_addr_1 = fields.Char(string="Bill Address Line 1")
    dp_bill_addr_2 = fields.Char(string="Bill Address Line 2")
    dp_bill_addr_state = fields.Char(string="Bill Address State")
    dp_bill_addr_postcode = fields.Char(string="Bill Address Postcode")
    dp_concession = fields.Boolean(string="Concession")
    dp_concession_card_type = fields.Char(string="Concession Card Type")
    dp_concession_card_no = fields.Char(string="Concession Card No")
    dp_concession_start_date = fields.Date(string="Concession Start Date")
    dp_concession_exp_date = fields.Date(string="Concession Expiry Date")
    dp_concession_first_name = fields.Char(string="Concession First Name")
    dp_concession_middle_name = fields.Char(string="Concession Middle Name")
    dp_concession_last_name = fields.Char(string="Concession Last Name")
    dp_product_code = fields.Char(string="Product Code")
    dp_meter_type = fields.Char(string="Meter Type")
    dp_kwh_usage_per_day = fields.Float(string="kWh Usage Per Day")
    dp_how_many_people = fields.Integer(string="Number of People")
    dp_how_many_bedrooms = fields.Integer(string="Number of Bedrooms")
    dp_solar_power = fields.Boolean(string="Solar Power")
    dp_solar_type = fields.Char(string="Solar Type")
    dp_solar_output = fields.Float(string="Solar Output")
    dp_green_energy = fields.Boolean(string="Green Energy")
    dp_winter_gas_usage = fields.Float(string="Winter Gas Usage")
    dp_summer_gas_usage = fields.Float(string="Summer Gas Usage")
    dp_monthly_winter_spend = fields.Float(string="Monthly Winter Spend")
    dp_monthly_summer_spend = fields.Float(string="Monthly Summer Spend")
    dp_invoice_method = fields.Selection([
        ('email', 'Email'),
        ('post', 'Post'),
        ('sms', 'SMS')
    ], string="Invoice Method")
    dp_customer_salutation = fields.Char(string="Customer Salutation")
    dp_first_name = fields.Char(string="First Name")
    dp_last_name = fields.Char(string="Last Name")
    dp_date_of_birth = fields.Date(string="Date of Birth")
    dp_email_contact = fields.Char(string="Email Contact")
    dp_contact_number = fields.Char(string="Contact Number")
    dp_hearing_impaired = fields.Boolean(string="Hearing Impaired", default=False)
    dp_secondary_contact = fields.Boolean(string="Secondary Contact", default=False)
    dp_secondary_salutation = fields.Char(string="Secondary Salutation")
    dp_secondary_first_name = fields.Char(string="Secondary First Name")
    dp_secondary_last_name = fields.Char(string="Secondary Last Name")
    dp_secondary_date_of_birth = fields.Date(string="Secondary Date of Birth")
    dp_secondary_email = fields.Char(string="Secondary Email")
    dp_referral_code = fields.Char(string="Referral Code")
    dp_new_username = fields.Char(string="New Username")
    dp_new_password = fields.Char(string="New Password")
    dp_customer_dlicense = fields.Char(string="Driver License")
    dp_customer_dlicense_state = fields.Char(string="DL State")
    dp_customer_dlicense_exp = fields.Date(string="DL Expiry")
    dp_customer_passport = fields.Char(string="Passport")
    dp_customer_passport_exp = fields.Date(string="Passport Expiry")
    dp_customer_medicare = fields.Char(string="Medicare")
    dp_customer_medicare_ref = fields.Char(string="Medicare Ref")
    dp_position_at_current_employer = fields.Char(string="Position at Current Employer")
    dp_employment_status = fields.Char(string="Employment Status")
    dp_current_employer = fields.Char(string="Current Employer")
    dp_employer_contact_number = fields.Char(string="Employer Contact Number")
    dp_years_in_employment = fields.Integer(string="Years in Employment")
    dp_months_in_employment = fields.Integer(string="Months in Employment")
    dp_employment_confirmation = fields.Boolean(string="Employment Confirmation")
    dp_life_support = fields.Boolean(string="Life Support", default=False)
    dp_life_support_machine_type = fields.Char(string="Life Support Machine Type")
    dp_life_support_details = fields.Text(string="Life Support Details")
    dp_nmi = fields.Char(string="NMI")
    dp_nmi_source = fields.Char(string="NMI Source")
    dp_mirn = fields.Char(string="MIRN")
    dp_mirn_source = fields.Char(string="MIRN Source")
    dp_connection_date = fields.Date(string="Connection Date")
    dp_electricity_connection = fields.Boolean(string="Electricity Connection")
    dp_gas_connection = fields.Boolean(string="Gas Connection")
    dp_12_month_disconnection = fields.Boolean(string="12 Month Disconnection")
    dp_cert_electrical_safety = fields.Boolean(string="Electrical Safety Cert")
    dp_cert_electrical_safety_id = fields.Char(string="Cert Electrical Safety ID")
    dp_cert_electrical_safety_sent = fields.Boolean(string="Cert Sent")
    dp_explicit_informed_consent = fields.Boolean(string="Explicit Informed Consent")
    dp_center_name = fields.Char(string="Center Name")
    dp_closer_name = fields.Char(string="Closer Name")
    dp_dnc_wash_number = fields.Char(string="DNC Wash Number")
    dp_dnc_exp_date = fields.Date(string="DNC Exp Date")
    dp_audit_1 = fields.Char(string="Audit-1")
    dp_audit_2 = fields.Char(string="Audit-2")
    dp_welcome_call = fields.Boolean(string="Welcome Call")  

    # MOMENTUM ENERGY FORM
    momentum_energy_transaction_reference = fields.Char("Transaction Reference")
    momentum_energy_transaction_channel = fields.Char("Transaction Channel")
    momentum_energy_transaction_date = fields.Datetime("Transaction Date")
    momentum_energy_transaction_verification_code = fields.Char("Transaction Verification Code")
    momentum_energy_transaction_source = fields.Char("Transaction Source")

    momentum_energy_customer_type = fields.Selection([
        ('resident', 'Resident'),
        ('company', 'Company')
    ], string="Customer Type", required=True)

    momentum_energy_customer_sub_type = fields.Char("Customer Sub Type")
    momentum_energy_communication_preference = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS')
    ], string="Communication Preference")
    momentum_energy_promotion_allowed = fields.Boolean("Promotion Allowed")
    momentum_energy_passport_id = fields.Char("Passport Number")
    momentum_energy_passport_expiry = fields.Date("Passport Expiry Date")
    momentum_energy_passport_country = fields.Char("Passport Issuing Country")
    momentum_energy_driving_license_id = fields.Char("Driving License Number")
    momentum_energy_driving_license_expiry = fields.Date("Driving License Expiry Date")
    momentum_energy_driving_license_state = fields.Char("Issuing State")
    momentum_energy_medicare_id = fields.Char("Medicare Number")
    momentum_energy_medicare_number = fields.Char("Medicare Document Number")
    momentum_energy_medicare_expiry = fields.Date("Medicare Expiry Date")
    momentum_energy_industry = fields.Char("Industry")
    momentum_energy_entity_name = fields.Char("Entity Name")
    momentum_energy_trading_name = fields.Char("Trading Name")
    momentum_energy_trustee_name = fields.Char("Trustee Name")
    momentum_energy_abn_document_id = fields.Char("ABN Document ID")
    momentum_energy_acn_document_id = fields.Char("ACN Document ID")
    momentum_energy_primary_contact_type = fields.Char("Primary Contact Type")
    momentum_energy_primary_salutation = fields.Char("Primary Salutation")
    momentum_energy_primary_first_name = fields.Char("Primary First Name")
    momentum_energy_primary_middle_name = fields.Char("Primary Middle Name")
    momentum_energy_primary_last_name = fields.Char("Primary Last Name")
    momentum_energy_primary_country_of_birth = fields.Char("Primary Country of Birth")
    momentum_energy_primary_date_of_birth = fields.Date("Primary Date of Birth")
    momentum_energy_primary_email = fields.Char("Primary Email")
    momentum_energy_primary_address_type = fields.Char("Primary Address Type")
    momentum_energy_primary_street_number = fields.Char("Primary Street Number")
    momentum_energy_primary_street_name = fields.Char("Primary Street Name")
    momentum_energy_primary_unit_number = fields.Char("Primary Unit Number")
    momentum_energy_primary_suburb = fields.Char("Primary Suburb")
    momentum_energy_primary_state = fields.Char("Primary State")
    momentum_energy_primary_post_code = fields.Char("Primary Post Code")
    momentum_energy_primary_phone_work = fields.Char("Primary Work Phone")
    momentum_energy_primary_phone_home = fields.Char("Primary Home Phone")
    momentum_energy_primary_phone_mobile = fields.Char("Primary Mobile Phone")
    momentum_energy_secondary_contact_type = fields.Char("Secondary Contact Type")
    momentum_energy_secondary_salutation = fields.Char("Secondary Salutation")
    momentum_energy_secondary_first_name = fields.Char("Secondary First Name")
    momentum_energy_secondary_middle_name = fields.Char("Secondary Middle Name")
    momentum_energy_secondary_last_name = fields.Char("Secondary Last Name")
    momentum_energy_secondary_country_of_birth = fields.Char("Secondary Country of Birth")
    momentum_energy_secondary_date_of_birth = fields.Date("Secondary Date of Birth")
    momentum_energy_secondary_email = fields.Char("Secondary Email")
    momentum_energy_secondary_address_type = fields.Char("Secondary Address Type")
    momentum_energy_secondary_street_number = fields.Char("Secondary Street Number")
    momentum_energy_secondary_street_name = fields.Char("Secondary Street Name")
    momentum_energy_secondary_unit_number = fields.Char("Secondary Unit Number")
    momentum_energy_secondary_suburb = fields.Char("Secondary Suburb")
    momentum_energy_secondary_state = fields.Char("Secondary State")
    momentum_energy_secondary_post_code = fields.Char("Secondary Post Code")
    momentum_energy_secondary_phone_work = fields.Char("Secondary Work Phone")
    momentum_energy_secondary_phone_home = fields.Char("Secondary Home Phone")
    momentum_energy_secondary_phone_mobile = fields.Char("Secondary Mobile Phone")
    momentum_energy_service_type = fields.Selection([
        ('power', 'Power'),
        ('gas', 'Gas'),
        ('other', 'Other')
    ], string="Service Type")
    momentum_energy_service_sub_type = fields.Char("Service Sub Type")
    momentum_energy_service_connection_id = fields.Char("Service Connection ID")
    momentum_energy_service_meter_id = fields.Char("Service Meter ID")
    momentum_energy_service_start_date = fields.Date("Service Start Date")
    momentum_energy_estimated_annual_kwhs = fields.Integer("Estimated Annual kWhs")
    momentum_energy_lot_number = fields.Char("Lot Number")
    momentum_energy_service_street_number = fields.Char("Service Street Number")
    momentum_energy_service_street_name = fields.Char("Service Street Name")
    momentum_energy_service_street_type_code = fields.Char("Service Street Type Code")
    momentum_energy_service_suburb = fields.Char("Service Suburb")
    momentum_energy_service_state = fields.Char("Service State")
    momentum_energy_service_post_code = fields.Char("Service Post Code")
    momentum_energy_service_access_instructions = fields.Text("Service Access Instructions")
    momentum_energy_service_safety_instructions = fields.Text("Service Safety Instructions")
    momentum_energy_offer_quote_date = fields.Datetime("Offer Quote Date")
    momentum_energy_service_offer_code = fields.Char("Service Offer Code")
    momentum_energy_service_plan_code = fields.Char("Service Plan Code")
    momentum_energy_contract_term_code = fields.Char("Contract Term Code")
    momentum_energy_contract_date = fields.Datetime("Contract Date")
    momentum_energy_payment_method = fields.Selection([
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer')
    ], string="Payment Method")
    momentum_energy_bill_cycle_code = fields.Char("Bill Cycle Code")
    momentum_energy_bill_delivery_method = fields.Selection([
        ('email', 'Email'),
        ('post', 'Post')
    ], string="Bill Delivery Method")

    #AMEX CREDIT CARD FIELDS
    cc_prefix = fields.Selection([
        ('n/a', 'N/A'), ('mr', 'Mr.'), ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('dr', 'Dr.'), ('miss', 'Miss')
    ], string="Prefix")
    cc_first_name = fields.Char("First Name")
    cc_last_name = fields.Char("Last Name")
    cc_job_title = fields.Char("Job Title")
    cc_phone = fields.Char("Phone")
    cc_email = fields.Char("Email")
    cc_annual_revenue = fields.Selection([
        ('under_2m', 'Under ~ $2M'), ('2m_10m', '$2M ~ $10M'), ('10m_50m', '$10M ~ $50M'), ('50m_100m', '$50M ~ $100M'), ('100m_above', 'Above $100M')
    ], string="Annual Revenue")
    cc_annual_spend = fields.Selection([
        ('under_1m', 'Under ~ $1M'), ('2m_5m', '$2M ~ $5M'), ('6m_10m', '$6M ~ $10M'),
        ('11m_15m', '$11M ~ $15M'), ('16m_20m', '$16M ~ $20M'),('20m_above', 'Above $20M')
    ], string="Annual Revenue")
    cc_existing_products = fields.Char("Existing Competitor Products")
    cc_expense_tools = fields.Char("Expense Management Tools")
    cc_additional_info = fields.Text("Additional information for sales team")
    cc_consent_personal_info = fields.Boolean(
        string="I have obtained the express consent of the above individual to provide their personal information as noted above to American Express for purposes of offering American Express Commercial Payment Products to the business of the individual."
    )
    cc_consent_contact_method = fields.Selection([
        ('phone', 'Phone'),
        ('email', 'Email')
    ], string="I have obtained the consent of above companies to contact the appointed representative via")

    cc_contact_preference = fields.Selection([
        ('me_first', 'Me first'),
        ('referred_first', 'The referred contact first')
    ], string="In order to best process this lead the salesperson should contact")



    # def read(self, fields=None, load='_classic_read'):
    #     """Override read to check and update lead stage when record is accessed"""
    #     result = super().read(fields, load)
        
    #     # Check if we need to update lead stage for each record
    #     for record in self:
    #         current_stage = record.lead_stage
            
    #         # Check if lead is in stage 1 but should be in stage 2
    #         if current_stage == '1' and record.en_name:
    #             _logger.info("Lead %s should be updated from stage 1 to stage 2", record.id)
    #             # Update to stage 2
    #             record.with_context(skip_stage_assign=True).write({'lead_stage': '2'})
    #             # Also trigger CRM stage assignment
    #             record._assign_lead_assigned_stage()
    #             _logger.info("Lead %s updated to stage 2", record.id)

    #         if current_stage == "2" and record.disposition == "sold_pending_quality":
    #             record.with_context(skip_stage_assign=True).write({'lead_stage':'3'}) 
        
    #     return result

    @api.model_create_multi
    def create(self, vals_list):
        """On create, use default stage and compute lead_stage"""
        _logger.info("Creating new leads: %s", vals_list)
        leads = super().create(vals_list)
        
        return leads

    def write(self, vals):
        """Override write to handle stage assignment after field updates"""
        _logger.info("Updating lead %s with values: %s", self.ids, vals)

        res = super().write(vals)

        # Skip stage assignment if context flag is set
        if self.env.context.get("skip_stage_assign"):
            return res

        Stage = self.env["crm.stage"]
        
        # Pre-fetch or create all possible stages ONCE before the loop
        stages_cache = {}
        stage_definitions = [
            ("Won", 12),
            ("On Hold", 13),
            ("Failed", 14),
            ("Call Back", 11),
            ("Lost", 6),
            ("Sold-Pending Quality", 8),
            ("Lead Assigned", 5)
        ]
        
        for stage_name, sequence in stage_definitions:
            stage = Stage.search([("name", "=", stage_name)], limit=1)
            if not stage:
                stage = Stage.create({"name": stage_name, "sequence": sequence})
            stages_cache[stage_name] = stage

        # Process each lead
        for lead in self:
            _logger.info("Processing lead: %s, lead_for: %s", lead.id, lead.lead_for)
            
            new_stage = None

            # STAGE 3 DISPOSITIONS
            if lead.lead_stage == "3":
                if lead.stage_3_dispostion == "closed":
                    new_stage = stages_cache["Won"]
                    _logger.info("Lead %s - Moving to Won stage", lead.id)
                elif lead.stage_3_dispostion == "on_hold":
                    new_stage = stages_cache["On Hold"]
                    _logger.info("Lead %s - Moving to On Hold stage", lead.id)
                elif lead.stage_3_dispostion == "failed":
                    new_stage = stages_cache["Failed"]
                    _logger.info("Lead %s - Moving to Failed stage", lead.id)
            
            # STAGE 2 DISPOSITIONS
            elif lead.lead_stage == "2":
                if lead.disposition == "callback":
                    new_stage = stages_cache["Call Back"]
                    _logger.info("Lead %s - Moving to Call Back stage", lead.id)
                elif lead.disposition == "lost":
                    new_stage = stages_cache["Lost"]
                    _logger.info("Lead %s - Moving to Lost stage", lead.id)
                elif lead.disposition == "sold_pending_quality":
                    new_stage = stages_cache["Sold-Pending Quality"]
                    lead.with_context(skip_stage_assign=True).write({"lead_stage":"3"})
                    _logger.info("Lead %s - Moving to Sold-Pending Quality stage", lead.id)
            

            elif lead.lead_stage == "1":
                if lead.en_name or lead.en_contact_number or lead.cc_prefix or lead.cc_first_name:
                    lead.with_context(skip_stage_assign=True).write({"lead_stage":"2"})
                    new_stage = stages_cache["Lead Assigned"]        

            # Apply stage update if needed
            if new_stage:
                if lead.stage_id.id != new_stage.id:
                    _logger.info("Applying stage update for lead %s: %s -> %s", 
                            lead.id, lead.stage_id.name, new_stage.name)
                    # Use SQL update to avoid recursion
                    self.env.cr.execute(
                        "UPDATE crm_lead SET stage_id = %s WHERE id = %s",
                        (new_stage.id, lead.id)
                    )
                    # Invalidate cache to ensure fresh data
                    lead.invalidate_recordset(['stage_id'])
            else:
                # Run normal stage assignment for other cases
                _logger.info("Running normal stage assignment for lead %s", lead.id)
                lead._assign_lead_assigned_stage()

        return res



    def _assign_lead_assigned_stage(self):
        """Move to 'Lead Assigned' CRM stage when Stage 1 is complete."""
        Stage = self.env["crm.stage"]
        
        for lead in self:
            
            if lead.lead_stage == "1" and lead.en_name or lead.en_contact_number:
                # Find or create "Lead Assigned" stage
                stage = Stage.search([("name", "=", "Lead Assigned")], limit=1)
                _logger.info("Stage EXISTS..............")
                if not stage:
                    _logger.info("Creating new 'Lead Assigned' stage")
                    stage = Stage.create({
                        "name": "Lead Assigned",
                        "sequence": 5,
                    })
                
                if lead.stage_id.id != stage.id:
                    _logger.info("Assigning lead %s to 'Lead Assigned' stage", lead.id)
                    lead.with_context(skip_stage_assign=True).write({"stage_id": stage.id})
                else:
                    _logger.info("Lead %s already in 'Lead Assigned' stage", lead.id)
            else:
                # Assign default CRM stage if none set and still in stage 1
                if not lead.stage_id:
                    default_stage = Stage.search([], order="sequence ASC", limit=1)
                    if default_stage:
                        _logger.info("Assigning lead %s to default stage: %s", lead.id, default_stage.name)
                        lead.with_context(skip_stage_assign=True).write({"stage_id": default_stage.id})


    #CREDIT CARD - AMEX FIELDS
    # amex_date = fields.Date(string="Date")
    # amex_center = fields.Char(string="Center")
    # amex_company_name = fields.Char(string="Company Name")
    # amex_abn = fields.Char(string="ABN")
    # amex_address_1 = fields.Char(string="Address Line 1")
    # amex_address_2 = fields.Char(string="Address Line 2")
    # amex_suburb = fields.Char(string="Suburb")
    # amex_state = fields.Char(string="State")
    # amex_country = fields.Char(string="Country")
    # amex_business_website = fields.Char(string="Website")
    # amex_saluation = fields.Selection([
    #     ('n/a', 'N/A'), 
    #     ('mr', 'Mr.'), 
    #     ('mrs', 'Mrs.'), 
    #     ('ms', 'Ms.'), 
    #     ('dr', 'Dr.'), 
    #     ('miss', 'Miss')
    # ], string="Prefix", default="mr")
    # amex_first_name = fields.Char(string="First Name")
    # amex_last_name = fields.Char(string="Last Name")
    # amex_position = fields.Char(string="Position in Business")
    # amex_contact = fields.Char(string="Contact Number")
    # amex_email = fields.Char(string="Email")
    # amex_current_turnover = fields.Char(string = "Current turnover less than 2 million or more")
    # amex_estimated_expense = fields.Char(string="Estimated Expenses On Card")
    # amex_existing_product = fields.Char(string="Existing Competitor Product")
    # amex_additional_info = fields.Char(string="Additional Information for Sales Team")
    # amex_tool_used =  fields.Char(string="Expense Management Tool Used")



