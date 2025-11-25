# from odoo import models, fields

# class ResUsers(models.Model):
#     _inherit = 'res.users'

#     vicidial_extension = fields.Char("Vicidial Extension")
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    # vicidial_extension = fields.Char("Vicidial Extension")

    lead_target_ids = fields.One2many('crm.lead.target', 'user_id', string='Lead Targets')
    lead_target_count = fields.Integer(string='Number of Targets', compute='_compute_lead_target_count')
    current_lead_target_id = fields.Many2one('crm.lead.target', string='Current Active Target', 
                                              compute='_compute_current_target', store=False)
    current_target_leads = fields.Integer(string='Current Target', related='current_lead_target_id.target_leads')
    current_achieved_leads = fields.Integer(string='Current Achieved', related='current_lead_target_id.achieved_leads')
    current_achievement_percentage = fields.Float(string='Current Achievement %', 
                                                   related='current_lead_target_id.achievement_percentage')

    
    
    @api.depends('lead_target_ids')
    def _compute_lead_target_count(self):
        for user in self:
            user.lead_target_count = len(user.lead_target_ids)

    @api.depends('lead_target_ids', 'lead_target_ids.state', 'lead_target_ids.date_start', 'lead_target_ids.date_end')
    def _compute_current_target(self):
        today = fields.Date.today()
        for user in self:
            current_target = self.env['crm.lead.target'].search([
                ('user_id', '=', user.id),
                ('state', '=', 'active'),
                ('date_start', '<=', today),
                ('date_end', '>=', today)
            ], limit=1, order='date_start desc')
            user.current_lead_target_id = current_target.id if current_target else False

    def action_view_lead_targets(self):
        """Open the user's lead targets"""
        self.ensure_one()
        return {
            'name': f'Lead Targets - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.target',
            'view_mode': 'list,form,kanban',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        }
# from odoo import models, fields, api


# class ResUsers(models.Model):
#     _inherit = 'res.users'

#     lead_target_ids = fields.One2many('crm.lead.target', 'user_id', string='Lead Targets')
#     lead_target_count = fields.Integer(string='Number of Targets', compute='_compute_lead_target_count')
#     current_lead_target_id = fields.Many2one('crm.lead.target', string='Current Active Target', 
#                                               compute='_compute_current_target', store=False)
#     current_target_leads = fields.Integer(string='Current Target', related='current_lead_target_id.target_leads')
#     current_achieved_leads = fields.Integer(string='Current Achieved', related='current_lead_target_id.achieved_leads')
#     current_achievement_percentage = fields.Float(string='Current Achievement %', 
#                                                    related='current_lead_target_id.achievement_percentage')

#     @api.depends('lead_target_ids')
#     def _compute_lead_target_count(self):
#         for user in self:
#             user.lead_target_count = len(user.lead_target_ids)

#     @api.depends('lead_target_ids', 'lead_target_ids.state', 'lead_target_ids.date_start', 'lead_target_ids.date_end')
#     def _compute_current_target(self):
#         today = fields.Date.today()
#         for user in self:
#             current_target = self.env['crm.lead.target'].search([
#                 ('user_id', '=', user.id),
#                 ('state', '=', 'active'),
#                 ('date_start', '<=', today),
#                 ('date_end', '>=', today)
#             ], limit=1, order='date_start desc')
#             user.current_lead_target_id = current_target.id if current_target else False

#     def action_view_lead_targets(self):
#         """Open the user's lead targets"""
#         self.ensure_one()
#         return {
#             'name': f'Lead Targets - {self.name}',
#             'type': 'ir.actions.act_window',
#             'res_model': 'crm.lead.target',
#             'view_mode': 'list,form,kanban',
#             'domain': [('user_id', '=', self.id)],
#             'context': {'default_user_id': self.id}
#         }