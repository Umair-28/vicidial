from odoo import models, fields


class HomeLoanData(models.Model):
    _name = 'custom.home.loan.data'
    _description = 'Stage-wise Home Loan Form Data'

    lead_id = fields.Many2one('crm.lead', string='lead')
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True)
    user_want_to = fields.Selection([
        ("refinance", "I want to refinance"),
        ("buy home", "I want to buy a home"),
    ],string="What would you like to do?")
    expected_price = fields.Integer(string="What is your exptected price?")
    deposit_amount = fields.Integer(string="How much deposit do you have?")
    buying_reason = fields.Selection([
        ("just_exploring", "Just exploring options"),
        ("planning_to_buy", "Planning to buy home in next 6 months"),
        ("actively_looking", "Actively looking/made an offer"),
        ("exchanged_contracts", "Exchanged Contracts"),
    ],string="What best describes your home buying situation?")
    first_home_buyer = fields.Boolean(string="Are you a first home buyer")
    property_type = fields.Selection([
        ("established_home", "Established Home"),
        ("newly_built", "Newly built/off the plan"),
        ("vacant_land", "Vacant land to build on"),
    ],string="What kind of property are you looking for?")   
    property_usage = fields.Selection([
        ("to_live", "I will live there"),
        ("for_investment", "It is for investment purposes"),
    ],string="How will this property be used?")
    credit_history = fields.Selection([
        ("excellent", "Excellent - no issues"),
        ("average", "Average paid default"),
        ("fair", "Fair"),
        ("don't know", "I don't know"),
    ],string="What do you think your credit history is?")
    income_source = fields.Selection([
        ("employee", "I am an employee"),
        ("business", "I have my own business"),
        ("other", "Other"),
    ],string="How do you earn your income?")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    contact = fields.Char(string="Contact Number")
    email = fields.Char(string="Email")
    accept_terms = fields.Boolean(string="Agree to accept terms and conditions")


