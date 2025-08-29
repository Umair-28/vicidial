from odoo import models, fields


class DodoPowerForm(models.Model):
    _name = 'custom.dodo.power.form'
    _description = 'DODO Power Form'

    lead_id = fields.Many2one('crm.lead', string='Lead')

    # Stage Tracking
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True)

    # Compliance / Internal
    internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    existing_sale = fields.Char(string="Existing Sale with NMI & Phone Number (Internal)")
    online_enquiry_form = fields.Char(string="Online Enquiry Form")

    # Sales Info
    sales_name = fields.Char(string="Sales Name")
    sales_reference = fields.Char(string="Sales Reference")
    agreement_date = fields.Date(string="Agreement Date")

    # Site / Address
    site_address_postcode = fields.Char(string="Site Address Postcode")
    site_addr_unit_type = fields.Char(string="Site Addr Unit Type")
    site_addr_unit_no = fields.Char(string="Site Addr Unit No")
    site_addr_floor_type = fields.Char(string="Site Addr Floor Type")
    site_addr_floor_no = fields.Char(string="Site Addr Floor No")
    site_addr_street_no = fields.Char(string="Site Addr Street No")
    site_addr_street_no_suffix = fields.Char(string="Site Addr Street No Suffix")
    site_addr_street_name = fields.Char(string="Site Addr Street Name")
    site_addr_street_type = fields.Char(string="Site Addr Street Type")
    site_addr_suburb = fields.Char(string="Site Addr Suburb")
    site_addr_state = fields.Char(string="Site Addr State")
    site_addr_postcode = fields.Char(string="Site Addr Postcode")
    site_addr_desc = fields.Text(string="Site Address Description")
    site_access = fields.Text(string="Site Access")
    site_more_than_12_months = fields.Boolean(string="At Site > 12 Months")

    # Previous Address
    prev_addr_1 = fields.Char(string="Previous Address Line 1")
    prev_addr_2 = fields.Char(string="Previous Address Line 2")
    prev_addr_state = fields.Char(string="Previous Address State")
    prev_addr_postcode = fields.Char(string="Previous Address Postcode")

    # Billing Address
    billing_address = fields.Boolean(string="Billing Address")
    bill_addr_1 = fields.Char(string="Bill Address Line 1")
    bill_addr_2 = fields.Char(string="Bill Address Line 2")
    bill_addr_state = fields.Char(string="Bill Address State")
    bill_addr_postcode = fields.Char(string="Bill Address Postcode")

    # Concessions
    concession = fields.Boolean(string="Concession")
    concession_card_type = fields.Char(string="Concession Card Type")
    concession_card_no = fields.Char(string="Concession Card No")
    concession_start_date = fields.Date(string="Concession Start Date")
    concession_exp_date = fields.Date(string="Concession Expiry Date")
    concession_first_name = fields.Char(string="Concession First Name")
    concession_middle_name = fields.Char(string="Concession Middle Name")
    concession_last_name = fields.Char(string="Concession Last Name")

    # Product / Energy Details
    product_code = fields.Char(string="Product Code")
    meter_type = fields.Char(string="Meter Type")
    kwh_usage_per_day = fields.Float(string="kWh Usage Per Day")
    how_many_people = fields.Integer(string="Number of People")
    how_many_bedrooms = fields.Integer(string="Number of Bedrooms")
    solar_power = fields.Boolean(string="Solar Power")
    solar_type = fields.Char(string="Solar Type")
    solar_output = fields.Float(string="Solar Output")
    green_energy = fields.Boolean(string="Green Energy")
    winter_gas_usage = fields.Float(string="Winter Gas Usage")
    summer_gas_usage = fields.Float(string="Summer Gas Usage")
    monthly_winter_spend = fields.Float(string="Monthly Winter Spend")
    monthly_summer_spend = fields.Float(string="Monthly Summer Spend")

    # Invoice
    invoice_method = fields.Selection([
        ('email', 'Email'),
        ('post', 'Post'),
        ('sms', 'SMS')
    ], string="Invoice Method")

    # Customer Info
    customer_salutation = fields.Char(string="Customer Salutation")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    date_of_birth = fields.Date(string="Date of Birth")
    email_contact = fields.Char(string="Email Contact")
    contact_number = fields.Char(string="Contact Number")
    hearing_impaired = fields.Boolean(string="Hearing Impaired", default=False)

    # Secondary Contact
    secondary_contact = fields.Boolean(string="Secondary Contact", default=False)
    secondary_salutation = fields.Char(string="Secondary Salutation")
    secondary_first_name = fields.Char(string="Secondary First Name")
    secondary_last_name = fields.Char(string="Secondary Last Name")
    secondary_date_of_birth = fields.Date(string="Secondary Date of Birth")
    secondary_email = fields.Char(string="Secondary Email")

    # Referral / Login
    referral_code = fields.Char(string="Referral Code")
    new_username = fields.Char(string="New Username")
    new_password = fields.Char(string="New Password")

    # Customer Identity
    customer_dlicense = fields.Char(string="Driver License")
    customer_dlicense_state = fields.Char(string="DL State")
    customer_dlicense_exp = fields.Date(string="DL Expiry")
    customer_passport = fields.Char(string="Passport")
    customer_passport_exp = fields.Date(string="Passport Expiry")
    customer_medicare = fields.Char(string="Medicare")
    customer_medicare_ref = fields.Char(string="Medicare Ref")

    # Employment
    position_at_current_employer = fields.Char(string="Position at Current Employer")
    employment_status = fields.Char(string="Employment Status")
    current_employer = fields.Char(string="Current Employer")
    employer_contact_number = fields.Char(string="Employer Contact Number")
    years_in_employment = fields.Integer(string="Years in Employment")
    months_in_employment = fields.Integer(string="Months in Employment")
    employment_confirmation = fields.Boolean(string="Employment Confirmation")

    # Life Support
    life_support = fields.Boolean(string="Life Support", default=False)
    life_support_machine_type = fields.Char(string="Life Support Machine Type")
    life_support_details = fields.Text(string="Life Support Details")

    # Energy Identifiers
    nmi = fields.Char(string="NMI")
    nmi_source = fields.Char(string="NMI Source")
    mirn = fields.Char(string="MIRN")
    mirn_source = fields.Char(string="MIRN Source")

    # Connection Info
    connection_date = fields.Date(string="Connection Date")
    electricity_connection = fields.Boolean(string="Electricity Connection")
    gas_connection = fields.Boolean(string="Gas Connection")
    twelve_month_disconnection = fields.Boolean(string="12 Month Disconnection")

    # Certificates
    cert_electrical_safety = fields.Boolean(string="Electrical Safety Cert")
    cert_electrical_safety_id = fields.Char(string="Cert Electrical Safety ID")
    cert_electrical_safety_sent = fields.Boolean(string="Cert Sent")

    # Consent
    explicit_informed_consent = fields.Boolean(string="Explicit Informed Consent")

    # Compliance / Audit
    center_name = fields.Char(string="Center Name")
    closer_name = fields.Char(string="Closer Name")
    dnc_wash_number = fields.Char(string="DNC Wash Number")
    dnc_exp_date = fields.Date(string="DNC Exp Date")
    audit_1 = fields.Char(string="Audit-1")
    audit_2 = fields.Char(string="Audit-2")
    welcome_call = fields.Boolean(string="Welcome Call")
