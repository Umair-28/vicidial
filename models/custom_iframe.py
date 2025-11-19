from odoo import models, fields, api

class CustomIframe(models.Model):
    _name = 'custom.iframe'
    _description = 'Vicidial Iframe Integration'

    name = fields.Char(default='Vicidial Session')

    user_id = fields.Many2one(
        'res.users',
        string="User",
        default=lambda self: self.env.user
    )

    sip_exten = fields.Char("SIP Extension")

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        user = self.env.user
        if 'user_id' in fields:
            defaults['user_id'] = user.id
        if 'sip_exten' in fields:
            defaults['sip_exten'] = user.vicidial_extension or user.x_studio_sip_extension or ''
        return defaults

    @api.onchange('user_id')
    def _onchange_user_id_set_extension(self):
        for rec in self:
            rec.sip_exten = rec.user_id.vicidial_extension or user.x_studio_sip_extension or ''

    lead_ids = fields.Many2many(
        'crm.lead',
        store=True,
        string="Matching Leads"
    )

    @api.depends('user_id')
    def _compute_sip_exten(self):
        for rec in self:
            rec.sip_exten = rec.user_id.vicidial_extension or user.x_studio_sip_extension or ''

    @api.depends('phone_number', 'user_id')
    def _compute_lead_ids(self):
        for rec in self:
            domain = [('phone', '=', rec.phone_number)]
            if rec.user_id:
                domain.append(('user_id', '=', rec.user_id.id))
            rec.lead_ids = self.env['crm.lead'].search(domain)


    @api.model
    def action_custom_iframe_backend(self):
        iframe = self.search([('user_id', '=', self.env.user.id)], limit=1)
        if not iframe:
            iframe = self.create({
                'user_id': self.env.user.id,
                'sip_exten': self.env.user.vicidial_extension or user.x_studio_sip_extension or '',
            })
        else:
            iframe.lead_ids = [(6, 0, [])]
            iframe.sip_exten =self.env.user.vicidial_extension or self.env.user.x_studio_sip_extension or ''
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vicidial',
            'res_model': 'custom.iframe',
            'view_mode': 'form',
            'res_id': iframe.id,
            'target': 'current',
        }


# Optional: Add iframe_id to crm.lead if needed
class CrmLead(models.Model):
    _inherit = 'crm.lead'

    iframe_id = fields.Many2one('custom.iframe', string="Vicidial Iframe Session")

# from odoo import models, fields, api

# class CustomIframe(models.Model):
#     _name = 'custom.iframe'
#     _description = 'Vicidial Iframe Integration'

#     name = fields.Char(default='Vicidial Session')

#     user_id = fields.Many2one(
#         'res.users',
#         string="User",
#         default=lambda self: self.env.user
#     )

#     sip_exten = fields.Char("SIP Extension")

#     @api.model
#     def default_get(self, fields):
#         defaults = super().default_get(fields)
#         user = self.env.user
#         if 'user_id' in fields:
#             defaults['user_id'] = user.id
#         if 'sip_exten' in fields:
#             defaults['sip_exten'] = user.vicidial_extension or ''
#         return defaults

#     @api.onchange('user_id')
#     def _onchange_user_id_set_extension(self):
#         for rec in self:
#             rec.sip_exten = rec.user_id.vicidial_extension or ''

#     lead_ids = fields.Many2many(
#         'crm.lead',
#         store=True,
#         string="Matching Leads"
#     )

#     @api.depends('user_id')
#     def _compute_sip_exten(self):
#         for rec in self:
#             rec.sip_exten = rec.user_id.vicidial_extension or ''

#     @api.depends('phone_number', 'user_id')
#     def _compute_lead_ids(self):
#         for rec in self:
#             domain = [('phone', '=', rec.phone_number)]
#             if rec.user_id:
#                 domain.append(('user_id', '=', rec.user_id.id))
#             rec.lead_ids = self.env['crm.lead'].search(domain)


#     @api.model
#     def action_custom_iframe_backend(self):
#         iframe = self.search([('user_id', '=', self.env.user.id)], limit=1)
#         if not iframe:
#             iframe = self.create({
#                 'user_id': self.env.user.id,
#                 'sip_exten': self.env.user.vicidial_extension or '',
#             })
#         else:
#             iframe.lead_ids = [(6, 0, [])]
#             iframe.sip_exten =self.env.user.vicidial_extension
#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'Vicidial',
#             'res_model': 'custom.iframe',
#             'view_mode': 'form',
#             'res_id': iframe.id,
#             'target': 'current',
#         }


# # Optional: Add iframe_id to crm.lead if needed
# class CrmLead(models.Model):
#     _inherit = 'crm.lead'

#     iframe_id = fields.Many2one('custom.iframe', string="Vicidial Iframe Session")


