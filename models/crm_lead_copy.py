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
        ('energy', 'Electicity & Gas'),
        ('optus_nbn', 'Optus NBN Form'),
    ],  required=True)

    @api.onchange('services')
    def _onchange_services(self):
        if self.services == "credit_card":
            _logger.info("User has selected credit card option")
        elif self.services == "energy":
            _logger.info("User has selected energy option")
        elif self.services == "optus_nbn":
            _logger.info("User has selected nbn option")
            


    # Core fields that trigger stage computation
    customer_name = fields.Char(string="Customer Name")
    customer_mobile_number = fields.Char(string="Customer Mobile Number")
    
    # Lead stage field - computed and stored
    lead_stage = fields.Selection([
        ("1", "Stage 1"),
        ("2", "Stage 2"),
        ("3", "Stage 3"),
        ("4", "Stage 4"),
    ], string="Lead Current Stage", default="1", store=True, readonly=True)

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
        ("dodo_nbn", "DODO NBN"),
        ("dodo_gas", "DODO & Gas"),
        ("first_energy", "1st energy"),
        ("optus", "Optus"),
        ("amex", "Amex"),
        ("momentum","Momentum")
    ],string="Campign Name", default="dodo_nbn")
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



    def read(self, fields=None, load='_classic_read'):
        """Override read to check and update lead stage when record is accessed"""
        result = super().read(fields, load)
        
        # Check if we need to update lead stage for each record
        for record in self:
            current_stage = record.lead_stage
            
            # Check if lead is in stage 1 but should be in stage 2
            if current_stage == '1' and record.en_name:
                _logger.info("Lead %s should be updated from stage 1 to stage 2", record.id)
                # Update to stage 2
                record.with_context(skip_stage_assign=True).write({'lead_stage': '2'})
                # Also trigger CRM stage assignment
                record._assign_lead_assigned_stage()
                _logger.info("Lead %s updated to stage 2", record.id)

            if current_stage == "2" and record.disposition == "sold_pending_quality":
                record.with_context(skip_stage_assign=True).write({'lead_stage':'3'}) 
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """On create, use default stage and compute lead_stage"""
        _logger.info("Creating new leads: %s", vals_list)
        leads = super().create(vals_list)
        
        return leads

    def write(self, vals):
        """Override write to handle stage assignment after field updates"""
        rainbow_leads = self.env["crm.lead"].browse()
        _logger.info("Updating lead %s with values: %s", self.ids, vals)
        # trigger_rainbow = (
        #     'stage_3_dispostion' in vals and 
        #     vals.get('stage_3_dispostion') == 'closed'
        # )

        res = super().write(vals)

        Stage = self.env["crm.stage"]
        for lead in self:
            _logger.info("Lead being saved: %s", lead.id)

            #LEAD CLOSED
            if lead.lead_stage == "3" and lead.stage_3_dispostion == "closed":
                closed_stage = Stage.search([("name","=","Won")],limit=1)
                if not closed_stage:
                    closed_stage = Stage.create({
                        "name":"Closed",
                        "sequence":12
                    })

                if lead.stage_id.id != closed_stage.id:
                    lead.with_context(skip_stage_assign=True).write({
                        "stage_id":closed_stage.id
                    })
                    

            #LEAD ONHOLD
            if lead.lead_stage == "3" and lead.stage_3_dispostion == "on_hold":
                hold_stage = Stage.search([("name","=","On Hold")],limit=1)
                if not hold_stage:
                    hold_stage = Stage.create({
                        "name":"On Hold",
                        "sequence":13
                    })

                if lead.stage_id.id != hold_stage.id:
                    lead.with_context(skip_stage_assign=True).write({
                        "stage_id":hold_stage.id
                    }) 

            #LEAD FAILED
            if lead.lead_stage == "3" and lead.stage_3_dispostion == "failed":
                failed_stage = Stage.search([("name","=","Failed")],limit=1)
                if not failed_stage:
                    failed_stage = Stage.create({
                        "name":"Failed",
                        "sequence":13
                    })

                if lead.stage_id.id != failed_stage.id:
                    lead.with_context(skip_stage_assign=True).write({
                        "stage_id":failed_stage.id
                    })                   

            # Call Back
            if lead.lead_stage == "2" and lead.disposition == "callback":
                callback_stage = Stage.search([("name", "=", "Call Back")], limit=1)
                if not callback_stage:
                    callback_stage = Stage.create({
                        "name": "Call Back",
                        "sequence": 11,
                    })

                if lead.stage_id.id != callback_stage.id:
                    _logger.info("Moving lead %s to Call Back stage", lead.id)
                    lead.with_context(skip_stage_assign=True).write({
                        "stage_id": callback_stage.id
                    })

            # Lost
            elif lead.lead_stage == "2" and lead.disposition == "lost":
                lost_stage = Stage.search([("name", "=", "Lost")], limit=1)
                if not lost_stage:
                    lost_stage = Stage.create({
                        "name": "Lost",
                        "sequence": 6,
                    })

                if lead.stage_id.id != lost_stage.id:
                    _logger.info("Moving lead %s to Lost stage", lead.id)
                    lead.with_context(skip_stage_assign=True).write({
                        "stage_id": lost_stage.id
                    })

            # Sold-Pending Quality
            elif lead.lead_stage == "2" and lead.disposition == "sold_pending_quality":
                pending = Stage.search([("name", "=", "Sold-Pending Quality")], limit=1)
                if not pending:
                    pending = Stage.create({
                        "name": "Sold-Pending Quality",
                        "sequence": 8,
                    })

                if lead.stage_id.id != pending.id:
                    _logger.info("Moving lead %s to Pending stage", lead.id)
                    lead.with_context(skip_stage_assign=True).write({
                        "stage_id": pending.id
                    })

            # ✅ Otherwise run your normal assignment
            elif not self.env.context.get("skip_stage_assign"):
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


    #                         #CREDIT CARD - AMEX FIELDS
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



