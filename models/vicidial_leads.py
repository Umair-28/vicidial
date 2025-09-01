from odoo import models, fields

class VicidialLead(models.Model):
    _name = "vicidial.lead"
    _description = "Vicidial Lead Data"

    lead_id = fields.Char(string="Lead ID", index=True)
    status = fields.Char(string="Status")
    entry_date = fields.Datetime(string="Entry Date")
    modify_date = fields.Datetime(string="Modify Date")
    agent_user = fields.Char(string="Agent User", index=True)
    user = fields.Char(string="User")
    vendor_lead_code = fields.Char(string="Vendor Lead Code")
    source_id = fields.Char(string="Source ID")
    list_id = fields.Char(string="List ID")
    gmt_offset_now = fields.Float(string="GMT Offset Now")
    called_since_last_reset = fields.Boolean(string="Called Since Last Reset")

    phone_code = fields.Char(string="Phone Code")
    phone_number = fields.Char(string="Phone Number", index=True)

    title = fields.Char(string="Title")
    first_name = fields.Char(string="First Name")
    middle_initial = fields.Char(string="Middle Initial")
    last_name = fields.Char(string="Last Name")

    address1 = fields.Char(string="Address 1")
    address2 = fields.Char(string="Address 2")
    address3 = fields.Char(string="Address 3")
    city = fields.Char(string="City")
    state = fields.Char(string="State")
    province = fields.Char(string="Province")
    postal_code = fields.Char(string="Postal Code")
    country_code = fields.Char(string="Country Code")

    gender = fields.Selection([
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ], string="Gender")

    date_of_birth = fields.Date(string="Date of Birth")

    alt_phone = fields.Char(string="Alt Phone")
    email = fields.Char(string="Email")
    security_phrase = fields.Char(string="Security Phrase")
    comments = fields.Text(string="Comments")

    called_count = fields.Integer(string="Called Count")
    last_local_call_time = fields.Datetime(string="Last Local Call Time")

    rank = fields.Integer(string="Rank")
    owner = fields.Char(string="Owner")
    entry_list_id = fields.Char(string="Entry List ID")
