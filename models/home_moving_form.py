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
    suburb = fields.Char("Suburb")
    state = fields.Char("State")
    postcode = fields.Char("Postcode")

    # Personal Details
    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    job_title = fields.Char("Job Title")
    dob = fields.Date("Date of Birth")
    friend_code = fields.Char("Refer a Friend Code")

    # Contact Details
    mobile = fields.Char("Mobile")
    work_phone = fields.Char("Work Phone")
    email = fields.Char("Email")
    how_heard = fields.Selection([
        ('google', 'Google'),
        ('social', 'Social Media'),
        ('friend', 'Friend Referral'),
        ('other', 'Other')
    ], string="How did you hear about us?")

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
