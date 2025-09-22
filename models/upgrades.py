from odoo import models, fields


class UpgradesForm(models.Model):
    _name = 'custom.upgrades.form'
    _description = 'Stage-wise Upgrades Form Data'

    lead_id = fields.Many2one('crm.lead', string='lead')
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True)  
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    mobile_no = fields.Char(string="Mobile No")
    email = fields.Char(string="Email")
    post_code = fields.Char("Post Code")
    interested_in = fields.Selection([
        ('air', 'Air Conitioning Rebate'),
        ('water_res','Hot Water System (Residential)'),
        ('water_com','Hot Water System (Commercial)')

    ], string="Rebate Interested In", default="air")
    how = fields.Text(string="How did you hear about us")
    accept_terms = fields.Boolean(string="By submitting your details you agree that you have read and agreed to the terms and conditions and privacy policy",default=False)








