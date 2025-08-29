from odoo import models, fields


class OptusBNBForm(models.Model):
    _name = 'custom.optus.nbn.form'
    _description = 'Optus NBN form'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True)
    sale_date = fields.Date(string="Sale Date")
    activation_date = fields.Date(string="Activation Date")
    order_no = fields.Char(string="Order Number")
    customer_name = fields.Char(string="Customer Name")
    service_address = fields.Char(string="Service Address")
    service = fields.Char(string="Service")
    plan = fields.Char(string="Plan")
    cost_per_month = fields.Float(string="Cost Per Month")  # better numeric
    center = fields.Char(string="Center")
    sales_person = fields.Char(string="Sales Person")
    contact_number = fields.Char(string="Contact Number")
    email = fields.Char(string="Email")
    notes = fields.Text(string="Notes")   # changed to Text
    dnc_ref_no = fields.Char(string="DNC Reference No")
    audit_1 = fields.Char(string="Audit 1")
    audit_2 = fields.Char(string="Audit 2")
