# from odoo import models, fields

# class ResUsers(models.Model):
#     _inherit = 'res.users'

#     vicidial_extension = fields.Char("Vicidial Extension")
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ResUsers(models.Model):
    _inherit = 'res.users'
    vicidial_extension = fields.Char("Vicidial Extension")

    lead_target_ids = fields.One2many('crm.lead.target', 'user_id', string='Lead Targets')
    lead_target_count = fields.Integer(string='Number of Targets', compute='_compute_lead_target_count')
    current_lead_target_id = fields.Many2one('crm.lead.target', string='Current Active Target', 
                                              compute='_compute_current_target', store=False)
    current_target_leads = fields.Integer(string='Current Target', related='current_lead_target_id.target_leads')
    current_achieved_leads = fields.Integer(string='Current Achieved', related='current_lead_target_id.achieved_leads')
    current_achievement_percentage = fields.Float(string='Current Achievement %', 
                                                   related='current_lead_target_id.achievement_percentage')
    auto_create_lead_target = fields.Boolean(string='Auto Create Lead Target', default=False,
                                              help='Automatically create monthly lead target for this user')
    default_lead_target = fields.Integer(string='Default Lead Target', default=10,
                                         help='Default number of leads for auto-created targets')

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

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        
        # Create lead target for new users if auto_create is enabled
        for user in users:
            if user.auto_create_lead_target:
                self._create_initial_lead_target(user)
        
        return users

    def _create_initial_lead_target(self, user):
        """Create initial monthly lead target for the user"""
        today = fields.Date.today()
        
        # Calculate end of current month
        end_date = today + relativedelta(months=1, days=-1)
        
        # Create the lead target
        self.env['crm.lead.target'].create({
            'user_id': user.id,
            'target_leads': user.default_lead_target or 10,
            'period_type': 'monthly',
            'date_start': today,
            'date_end': end_date,
            'state': 'active',
        })

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

#     vicidial_extension = fields.Char("Vicidial Extension")
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
