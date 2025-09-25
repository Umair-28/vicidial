from odoo import models, fields


class MomentumEnergyForm(models.Model):
    _name = 'momentum.energy.form'
    _description = 'Momentum Energy Form'

    lead_id = fields.Many2one('crm.lead', string='Lead')

    # Stage Tracking
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True, default='1')

    # ========================
    # Transaction Info
    # ========================
    transaction_reference = fields.Char("Transaction Reference")
    transaction_channel = fields.Char("Transaction Channel")
    transaction_date = fields.Datetime("Transaction Date")
    transaction_verification_code = fields.Char("Transaction Verification Code")
    transaction_source = fields.Char("Transaction Source")

    # ========================
    # Customer Info
    # ========================
    customer_type = fields.Selection([
        ('resident', 'Resident'),
        ('company', 'Company')
    ], string="Customer Type", required=True)

    customer_sub_type = fields.Char("Customer Sub Type")
    communication_preference = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS')
    ], string="Communication Preference")
    promotion_allowed = fields.Boolean("Promotion Allowed")

    # -------- Resident Identity --------
    passport_id = fields.Char("Passport Number")
    passport_expiry = fields.Date("Passport Expiry Date")
    passport_country = fields.Char("Passport Issuing Country")

    driving_license_id = fields.Char("Driving License Number")
    driving_license_expiry = fields.Date("Driving License Expiry Date")
    driving_license_state = fields.Char("Issuing State")

    medicare_id = fields.Char("Medicare Number")
    medicare_number = fields.Char("Medicare Document Number")
    medicare_expiry = fields.Date("Medicare Expiry Date")

    # -------- Company Identity --------
    industry = fields.Char("Industry")
    entity_name = fields.Char("Entity Name")
    trading_name = fields.Char("Trading Name")
    trustee_name = fields.Char("Trustee Name")
    abn_document_id = fields.Char("ABN Document ID")
    acn_document_id = fields.Char("ACN Document ID")

    # ========================
    # Primary Contact
    # ========================
    primary_contact_type = fields.Char("Primary Contact Type")
    primary_salutation = fields.Char("Primary Salutation")
    primary_first_name = fields.Char("Primary First Name")
    primary_middle_name = fields.Char("Primary Middle Name")
    primary_last_name = fields.Char("Primary Last Name")
    primary_country_of_birth = fields.Char("Primary Country of Birth")
    primary_date_of_birth = fields.Date("Primary Date of Birth")
    primary_email = fields.Char("Primary Email")

    # Primary Address
    primary_address_type = fields.Char("Primary Address Type")
    primary_street_number = fields.Char("Primary Street Number")
    primary_street_name = fields.Char("Primary Street Name")
    primary_unit_number = fields.Char("Primary Unit Number")
    primary_suburb = fields.Char("Primary Suburb")
    primary_state = fields.Char("Primary State")
    primary_post_code = fields.Char("Primary Post Code")

    # Primary Phones
    primary_phone_work = fields.Char("Primary Work Phone")
    primary_phone_home = fields.Char("Primary Home Phone")
    primary_phone_mobile = fields.Char("Primary Mobile Phone")

    # ========================
    # Secondary Contact
    # ========================
    secondary_contact_type = fields.Char("Secondary Contact Type")
    secondary_salutation = fields.Char("Secondary Salutation")
    secondary_first_name = fields.Char("Secondary First Name")
    secondary_middle_name = fields.Char("Secondary Middle Name")
    secondary_last_name = fields.Char("Secondary Last Name")
    secondary_country_of_birth = fields.Char("Secondary Country of Birth")
    secondary_date_of_birth = fields.Date("Secondary Date of Birth")
    secondary_email = fields.Char("Secondary Email")

    # Secondary Address
    secondary_address_type = fields.Char("Secondary Address Type")
    secondary_street_number = fields.Char("Secondary Street Number")
    secondary_street_name = fields.Char("Secondary Street Name")
    secondary_unit_number = fields.Char("Secondary Unit Number")
    secondary_suburb = fields.Char("Secondary Suburb")
    secondary_state = fields.Char("Secondary State")
    secondary_post_code = fields.Char("Secondary Post Code")

    # Secondary Phones
    secondary_phone_work = fields.Char("Secondary Work Phone")
    secondary_phone_home = fields.Char("Secondary Home Phone")
    secondary_phone_mobile = fields.Char("Secondary Mobile Phone")

    # ========================
    # Service Info
    # ========================
    service_type = fields.Selection([
        ('power', 'Power'),
        ('gas', 'Gas'),
        ('other', 'Other')
    ], string="Service Type")

    service_sub_type = fields.Char("Service Sub Type")
    service_connection_id = fields.Char("Service Connection ID")
    service_meter_id = fields.Char("Service Meter ID")
    service_start_date = fields.Date("Service Start Date")
    estimated_annual_kwhs = fields.Integer("Estimated Annual kWhs")
    lot_number = fields.Char("Lot Number")

    # Serviced Address
    service_street_number = fields.Char("Service Street Number")
    service_street_name = fields.Char("Service Street Name")
    service_street_type_code = fields.Char("Service Street Type Code")
    service_suburb = fields.Char("Service Suburb")
    service_state = fields.Char("Service State")
    service_post_code = fields.Char("Service Post Code")
    service_access_instructions = fields.Text("Service Access Instructions")
    service_safety_instructions = fields.Text("Service Safety Instructions")

    # Billing Info
    offer_quote_date = fields.Datetime("Offer Quote Date")
    service_offer_code = fields.Char("Service Offer Code")
    service_plan_code = fields.Char("Service Plan Code")
    contract_term_code = fields.Char("Contract Term Code")
    contract_date = fields.Datetime("Contract Date")
    payment_method = fields.Selection([
        ('cheque', 'Cheque'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer')
    ], string="Payment Method")
    bill_cycle_code = fields.Char("Bill Cycle Code")
    bill_delivery_method = fields.Selection([
        ('email', 'Email'),
        ('post', 'Post')
    ], string="Bill Delivery Method")


    
