from odoo import models, fields

class CustomHomeMovingForm(models.Model):
    _name = 'custom.home.moving.form'
    _description = 'Home Moving Form'

    lead_id = fields.Many2one('crm.lead', string="Lead")
    stage = fields.Selection(
        [('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
        string="Stage"
    )

    # Moving Details
    moving_date = fields.Date("Moving Date")
    address = fields.Char("Address")
    property_type = fields.Selection([
        ('business',"Business"),
        ('residential',"Residential"),
    ],string="What type of propery")
    ownership =  fields.Selection([
        ('own',"Own"),
        ('rent',"Rent"),
    ],string="Property Ownership")

    # Personal Details
    status = fields.Selection([
        ('n/a',"N/A"),
        ('dr',"Dr."),
        ('mr',"Mr."),
        ('mrs',"Mrs."),
        ('ms',"Ms."),
        ('miss',"Miss."),

    ],string="Status")
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    job_title = fields.Char("Job Title")
    dob = fields.Date("Date of Birth")

    # Contact Details
    mobile = fields.Char("Mobile")
    work_phone = fields.Char("Work Phone")
    home_phone = fields.Char("Home Phone")
    email = fields.Char("Email")
    how_heard = fields.Selection([
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('word_of_mouth', 'Word of Mouth'),
        ('real_estate', "Real Estate"),
        ('other', 'Other')
    ], string="How did you hear about us?")

    #Real Estate Info
    agency_name = fields.Char("Real estate agency name")
    broker_name = fields.Char("Broker name")
    agency_contact_number = fields.Char("Real estate contact number")
    # Services
    connect_electricity = fields.Boolean("Electricity")
    connect_gas = fields.Boolean("Gas")
    connect_internet = fields.Boolean("Internet")
    connect_water = fields.Boolean("Water")
    connect_tv = fields.Boolean("Pay TV")
    connect_removalist = fields.Boolean("Removalist")

    # Consent
    accept_terms = fields.Boolean("I accept the Terms and Conditions")
    recaptcha_checked = fields.Boolean("I'm not a robot")
