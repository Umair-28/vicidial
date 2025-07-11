from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    vicidial_extension = fields.Char("Vicidial Extension")
