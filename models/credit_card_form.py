from odoo import models, fields

class CreditCardForm(models.Model):
    _name = 'custom.credit.card.form'
    _description = 'Credit Card Form Submission'

    lead_id = fields.Many2one('crm.lead', string="Lead Reference")


    prefix = fields.Selection([
        ('n/a', 'N/A'), ('mr', 'Mr.'), ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('dr', 'Dr.'), ('miss', 'Miss')
    ], string="Prefix")
    
    stage = fields.Selection(
    [('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Stage",
    default='1',
    required=True)

    first_name = fields.Char("First Name")
    last_name = fields.Char("Last Name")
    job_title = fields.Char("Job Title")
    phone = fields.Char("Phone")
    email = fields.Char("Email")

    annual_revenue = fields.Selection([
        ('under_2m', 'Under ~ $2M'), ('2m_10m', '$2M ~ $10M'), ('10m_50m', '$10M ~ $50M'),
        ('50m_100m', '$50M ~ $100M'), ('100m_above', 'Above $100M')
    ], string="Annual Revenue")

    annual_spend = fields.Char("Annual Spend")
    existing_products = fields.Char("Existing Competitor Products")
    expense_tools = fields.Char("Expense Management Tools")
    additional_info = fields.Text("Additional information for sales team")

    consent_personal_info = fields.Boolean()
    consent_contact_method = fields.Selection([
        ('phone', 'Phone'),
        ('email', 'Email')
    ])

    contact_preference = fields.Selection([
        ('me_first', 'Me first'),
        ('referred_first', 'The referred contact first')
    ])
