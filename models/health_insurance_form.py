from odoo import models, fields


class HealthInsuranceFormData(models.Model):
    _name = 'custom.health.insurance.form.data'
    _description = 'Broadband Form Data'

    lead_id = fields.Many2one('crm.lead', string='Lead')

    stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5'),
    ], string='Stage')

    current_address = fields.Char(string="Current address")
    cover_type = fields.Selection([
        ("hospital_extras", "Hospital + Extras"),
        ("hospital", "Hospital only"),
        ("extras", "Extras only"),
    ],string="Select type of cover")
    have_insurance_cover = fields.Selection([
        ("yes","Yes"),
        ("no","No")
    ],string="Do you have health inssurance cover")
    insurance_considerations = fields.Selection([
        ("health_concern","I have a specific health concern"),
        ("save_money","I am looking to save money on my health premium"),
        ("no_insurance_before","I haven't held health insurance before"),
        ("better_health_cover","I am looking for better health cover"),
        ("need_for_tax","I need it for my tax"),
        ("planning_a_baby","I am planning a baby"),
        ("changed_circumstances","My circumstances have changed"),
        ("compare_options","I just want to compare options"),
    ],string="What are your main considerations when looking for a new health insurance cover?")
    dob = fields.Date(string="What is your date of birth")
    annual_taxable_income = fields.Selection([
        ("$97,000_or_less","$97,000 or less (Base Tier)"),
        ("$97,001_$113,000","$97,001 - $113,000 (Tier 1)"),
        ("$113,001_$151,000","$113,001 - $151,000 (Tier 2)"),
        ("$151,001_or_more","$151,001 or more (Tier 3)")
    ],string="What is your annual taxable income?")
    full_name = fields.Char(string="Full Name")
    contact_number = fields.Char(string="Contact Number")
    email = fields.Char(string="Email")