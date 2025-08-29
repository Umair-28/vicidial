from odoo import models, fields


class DodoNBNForm(models.Model):
    _name = 'custom.dodo.nbn.form'
    _description = 'Stage-wise DODO NBN Form Data'

    lead_id = fields.Many2one('crm.lead', string='lead')
    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='Stage', required=True)
    dodo_receipt_no = fields.Char(string="DODO Receipt Number")
    service_type = fields.Char(string="Service Type")
    plan_sold_with_dodo = fields.Char(string="Plan With DODO")
    current_provider = fields.Char(string="Current Provider")
    current_provider_acc_no = fields.Char(string="Current Provider Account No")
    title = fields.Selection([
        ("mr", "MR"),
        ("mrs", "MRS"),
    ],string="Title")   
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    mobile_no = fields.Char(string="Mobile No")
    installation_address = fields.Char(string="Installation Address - Unit/Flat Number")
    house_number = fields.Char(string="House No")
    street_name = fields.Char(string="Street Name")
    street_type = fields.Char(string="Street Type")
    suburb = fields.Char(string="Installation address-Suburb")
    state = fields.Char(string="State")
    post_code = fields.Char("Post Code")
    sale_date = fields.Date(string="Sale Date")
    center_name = fields.Char(string="Center Name")
    closer_name = fields.Char(string="Closer Name")
    dnc_ref_no = fields.Char(string="DNC Reference No")
    dnc_exp_date = fields.Date(string="DNC Expiry Date")
    audit_1 = fields.Char(string="Audit 1")
    audit_2 = fields.Char(string="Audit 2")








