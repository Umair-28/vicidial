from odoo import models, fields


class BroadbandFormData(models.Model):
    _name = 'custom.broadband.form.data'
    _description = 'Broadband Form Data'

    lead_id = fields.Many2one('crm.lead', string='Lead')

    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5'),
    ], string='Stage')

    current_address = fields.Char(string="Current Address")
    internet_usage_type = fields.Selection([
        ("browsing_email", "Browsing and Email"),
        ("work", "Work and Study"),
        ("social_media", "Social Media"),
        ("gaming", "Online Gaming"),
        ("streaming", "Streaming video/TV/Movies")       
    ], string="How will you use this internet?")

    internet_users_count = fields.Integer(string="How many people will be using the internet?")
    important_feature = fields.Selection([
        ("speed", "Speed"),
        ("price", "Price"),
        ("reliability", "Reliability"),      
    ], string="What is the most important feature to you?")
    speed_preference = fields.Selection([
        ("25Mb", "25 Mbps"),
        ("50Mb", "50 Mbps"),
        ("100Mb", "100 Mbps"),
        ("not_sure", "Not Sure"),   
    ], string="Do you have a speed preference?")
    broadband_reason = fields.Selection([
        ("moving", "I am Moving"),
        ("better_plan", "I want a better plan"),
        ("connection", "I need broadband connected"),
    ], string="Why are you looking into your broadband options?")
    when_to_connect_type = fields.Selection([
        ("asap", "ASAP"),
        ("dont_mind", "I don't mind"),
        ("specific_date", "Choose a date"),
    ], string="When to Connect")
    when_to_connect_date = fields.Date(string="Preferred Connection Date")
    compare_plans = fields.Boolean()
    name = fields.Char(string="Full Name")
    contact_number = fields.Char(string="Contact Number")
    email = fields.Char(string="Email")
    request_callback = fields.Boolean(string="Request Callback?")
    accept_terms = fields.Boolean(string="Accept Terms?")

    
