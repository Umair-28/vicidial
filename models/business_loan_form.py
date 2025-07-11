from odoo import models, fields


class CustomBusinessLoanData(models.Model):
    _name = 'custom.business.loan.data'
    _description = 'Stage-wise Business Loan Form Data'

    lead_id = fields.Many2one('crm.lead', string='lead')
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True)
    amount_to_borrow = fields.Integer(string="How much would you like to borrow?")
    business_name = fields.Char(string="Name of your business")
    trading_duration = fields.Selection([
        ("0-6 months", "0-6 Months"),
        ("6-12 months", "6-12 Months"),
        ("12-24 months", "12-24 Months"),
        ("over 24 months", "Over 24 Months"),
    ],string="How long have you been trading")
    monthly_turnover = fields.Integer(string="What is your monthly turnover")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    email = fields.Char(string="Email")
    home_owner = fields.Boolean(string="Are you a home owner?")
    accept_terms = fields.Boolean(string="Accept terms and conditions")


