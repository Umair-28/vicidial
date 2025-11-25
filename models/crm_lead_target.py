from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class CrmLeadTarget(models.Model):
    _name = 'crm.lead.target'
    _description = 'Individual Lead Target'
    _order = 'date_start desc'

    name = fields.Char(string='Target Name', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', required=True, ondelete='cascade')
    target_leads = fields.Integer(string='Target Leads', required=True, default=0)
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Period')
    ], string='Period Type', default='monthly', required=True)
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True)
    achieved_leads = fields.Integer(string='Achieved Leads', compute='_compute_achieved_leads', store=False)
    won_lead_ids = fields.Many2many('crm.lead', string='Won Leads', compute='_compute_won_lead_ids', store=False)
    achievement_percentage = fields.Float(string='Achievement %', compute='_compute_achievement_percentage', store=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed')
    ], string='Status', default='draft')
    
    @api.depends('user_id', 'period_type', 'date_start')
    def _compute_name(self):
        for record in self:
            if record.user_id and record.period_type:
                period_name = dict(record._fields['period_type'].selection).get(record.period_type)
                record.name = f"{record.user_id.name} - {period_name} Target"
            else:
                record.name = "New Target"
    
    @api.onchange('period_type', 'date_start')
    def _onchange_period_type(self):
        if self.date_start and self.period_type:
            start_date = fields.Date.from_string(self.date_start)
            if self.period_type == 'monthly':
                # Last day of the month using relativedelta
                end_date = start_date + relativedelta(months=1, days=-1)
                self.date_end = end_date
            elif self.period_type == 'quarterly':
                # 3 months from start (last day of 3rd month)
                end_date = start_date + relativedelta(months=3, days=-1)
                self.date_end = end_date
            elif self.period_type == 'yearly':
                # 1 year from start (last day of 12th month)
                end_date = start_date + relativedelta(years=1, days=-1)
                self.date_end = end_date
    
    def _compute_achieved_leads(self):
        for record in self:
            # Find the "Sale Closed" stage - try multiple possible names
            won_stage = self.env['crm.stage'].search([
                '|', '|', '|',
                ('name', '=', 'Sale Closed'),
                ('name', '=', 'Won'),
                ('name', '=', 'Closed Won'),
                ('is_won', '=', True)
            ], limit=1)
            
            if won_stage:
                # Count leads in won stage, check both date_closed and write_date
                domain = [
                    ('user_id', '=', record.user_id.id),
                    ('stage_id', '=', won_stage.id),
                ]
                
                # Get all won leads for this user
                won_leads = self.env['crm.lead'].search(domain)
                
                # Filter by date - check date_closed first, then write_date as fallback
                count = 0
                for lead in won_leads:
                    check_date = lead.date_closed if lead.date_closed else lead.write_date
                    if check_date:
                        check_date_only = check_date.date()
                        if record.date_start <= check_date_only <= record.date_end:
                            count += 1
                
                record.achieved_leads = count
            else:
                # Fallback: count by probability
                domain = [
                    ('user_id', '=', record.user_id.id),
                    ('probability', '=', 100),
                ]
                
                won_leads = self.env['crm.lead'].search(domain)
                count = 0
                for lead in won_leads:
                    check_date = lead.date_closed if lead.date_closed else lead.write_date
                    if check_date:
                        check_date_only = check_date.date()
                        if record.date_start <= check_date_only <= record.date_end:
                            count += 1
                
                record.achieved_leads = count
    
    @api.depends('achieved_leads', 'target_leads')
    def _compute_achievement_percentage(self):
        for record in self:
            if record.target_leads > 0:
                record.achievement_percentage = (record.achieved_leads / record.target_leads) * 100
            else:
                record.achievement_percentage = 0.0
    
    def action_activate(self):
        self.write({'state': 'active'})
    
    def action_complete(self):
        self.write({'state': 'completed'})

    @api.depends('user_id', 'date_start', 'date_end')
    def _compute_won_lead_ids(self):
        for record in self:
            # Find won stage
            won_stage = self.env['crm.stage'].search([
                '|', '|', '|',
                ('name', '=', 'Sale Closed'),
                ('name', '=', 'Won'),
                ('name', '=', 'Closed Won'),
                ('is_won', '=', True)
            ], limit=1)

            if won_stage:
                domain = [
                    ('user_id', '=', record.user_id.id),
                    ('stage_id', '=', won_stage.id),
                ]
            else:
                domain = [
                    ('user_id', '=', record.user_id.id),
                    ('probability', '=', 100),
                ]

            leads = self.env['crm.lead'].search(domain)

            # filter by date range
            filtered = leads.filtered(lambda l:
                (l.date_closed or l.write_date).date() >= record.date_start and
                (l.date_closed or l.write_date).date() <= record.date_end
            )

            record.won_lead_ids = filtered
    
    
    def action_view_leads(self):
        """Open the list of leads for this target period"""
        self.ensure_one()
        
        # Find the "Sale Closed" stage - try multiple possible names
        won_stage = self.env['crm.stage'].search([
            '|', '|', '|',
            ('name', '=', 'Sale Closed'),
            ('name', '=', 'Won'),
            ('name', '=', 'Closed Won'),
            ('is_won', '=', True)
        ], limit=1)
        
        if won_stage:
            domain = [
                ('user_id', '=', self.user_id.id),
                ('stage_id', '=', won_stage.id),
            ]
        else:
            # Fallback
            domain = [
                ('user_id', '=', self.user_id.id),
                ('probability', '=', 100),
            ]
        
        return {
            'name': f'Won Leads for {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,form,kanban',
            'domain': domain,
            'context': {'default_user_id': self.user_id.id}
        }


# from odoo import models, fields, api
# from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta


# class CrmLeadTarget(models.Model):
#     _name = 'crm.lead.target'
#     _description = 'Individual Lead Target'
#     _order = 'date_start desc'

#     name = fields.Char(string='Target Name', compute='_compute_name', store=True)
#     user_id = fields.Many2one('res.users', string='Salesperson', required=True, ondelete='cascade')
#     target_leads = fields.Integer(string='Target Leads', required=True, default=0)
#     period_type = fields.Selection([
#         ('monthly', 'Monthly'),
#         ('quarterly', 'Quarterly'),
#         ('yearly', 'Yearly'),
#         ('custom', 'Custom Period')
#     ], string='Period Type', default='monthly', required=True)
#     date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
#     date_end = fields.Date(string='End Date', required=True)
#     achieved_leads = fields.Integer(string='Achieved Leads', compute='_compute_achieved_leads', store=False)
#     achievement_percentage = fields.Float(string='Achievement %', compute='_compute_achievement_percentage', store=False)
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('active', 'Active'),
#         ('completed', 'Completed')
#     ], string='Status', default='draft')
    
#     @api.depends('user_id', 'period_type', 'date_start')
#     def _compute_name(self):
#         for record in self:
#             if record.user_id and record.period_type:
#                 period_name = dict(record._fields['period_type'].selection).get(record.period_type)
#                 record.name = f"{record.user_id.name} - {period_name} Target"
#             else:
#                 record.name = "New Target"
    
#     @api.onchange('period_type', 'date_start')
#     def _onchange_period_type(self):
#         if self.date_start and self.period_type:
#             start_date = fields.Date.from_string(self.date_start)
#             if self.period_type == 'monthly':
#                 # Last day of the month using relativedelta
#                 end_date = start_date + relativedelta(months=1, days=-1)
#                 self.date_end = end_date
#             elif self.period_type == 'quarterly':
#                 # 3 months from start (last day of 3rd month)
#                 end_date = start_date + relativedelta(months=3, days=-1)
#                 self.date_end = end_date
#             elif self.period_type == 'yearly':
#                 # 1 year from start (last day of 12th month)
#                 end_date = start_date + relativedelta(years=1, days=-1)
#                 self.date_end = end_date
    
#     def _compute_achieved_leads(self):
#         for record in self:
#             # Find the "Sale Closed" stage - try multiple possible names
#             won_stage = self.env['crm.stage'].search([
#                 '|', '|', '|',
#                 ('name', '=', 'Sale Closed'),
#                 ('name', '=', 'Won'),
#                 ('name', '=', 'Closed Won'),
#                 ('is_won', '=', True)
#             ], limit=1)
            
#             if won_stage:
#                 # Count leads in won stage, check both date_closed and write_date
#                 domain = [
#                     ('user_id', '=', record.user_id.id),
#                     ('stage_id', '=', won_stage.id),
#                 ]
                
#                 # Get all won leads for this user
#                 won_leads = self.env['crm.lead'].search(domain)
                
#                 # Filter by date - check date_closed first, then write_date as fallback
#                 count = 0
#                 for lead in won_leads:
#                     check_date = lead.date_closed if lead.date_closed else lead.write_date
#                     if check_date:
#                         check_date_only = check_date.date()
#                         if record.date_start <= check_date_only <= record.date_end:
#                             count += 1
                
#                 record.achieved_leads = count
#             else:
#                 # Fallback: count by probability
#                 domain = [
#                     ('user_id', '=', record.user_id.id),
#                     ('probability', '=', 100),
#                 ]
                
#                 won_leads = self.env['crm.lead'].search(domain)
#                 count = 0
#                 for lead in won_leads:
#                     check_date = lead.date_closed if lead.date_closed else lead.write_date
#                     if check_date:
#                         check_date_only = check_date.date()
#                         if record.date_start <= check_date_only <= record.date_end:
#                             count += 1
                
#                 record.achieved_leads = count
    
#     @api.depends('achieved_leads', 'target_leads')
#     def _compute_achievement_percentage(self):
#         for record in self:
#             if record.target_leads > 0:
#                 record.achievement_percentage = (record.achieved_leads / record.target_leads) * 100
#             else:
#                 record.achievement_percentage = 0.0
    
#     def action_activate(self):
#         self.write({'state': 'active'})
    
#     def action_complete(self):
#         self.write({'state': 'completed'})
    
#     def action_view_leads(self):
#         """Open the list of leads for this target period"""
#         self.ensure_one()
        
#         # Find the "Sale Closed" stage - try multiple possible names
#         won_stage = self.env['crm.stage'].search([
#             '|', '|', '|',
#             ('name', '=', 'Sale Closed'),
#             ('name', '=', 'Won'),
#             ('name', '=', 'Closed Won'),
#             ('is_won', '=', True)
#         ], limit=1)
        
#         if won_stage:
#             domain = [
#                 ('user_id', '=', self.user_id.id),
#                 ('stage_id', '=', won_stage.id),
#             ]
#         else:
#             # Fallback
#             domain = [
#                 ('user_id', '=', self.user_id.id),
#                 ('probability', '=', 100),
#             ]
        
#         return {
#             'name': f'Won Leads for {self.user_id.name}',
#             'type': 'ir.actions.act_window',
#             'res_model': 'crm.lead',
#             'view_mode': 'list,form,kanban',
#             'domain': domain,
#             'context': {'default_user_id': self.user_id.id}
#         }
















# from odoo import models, fields, api
# from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta


# class CrmLeadTarget(models.Model):
#     _name = 'crm.lead.target'
#     _description = 'Individual Lead Target'
#     _order = 'date_start desc'

#     name = fields.Char(string='Target Name', compute='_compute_name', store=True)
#     user_id = fields.Many2one('res.users', string='Salesperson', required=True, ondelete='cascade')
#     target_leads = fields.Integer(string='Target Leads', required=True, default=0)
#     period_type = fields.Selection([
#         ('monthly', 'Monthly'),
#         ('quarterly', 'Quarterly'),
#         ('yearly', 'Yearly'),
#         ('custom', 'Custom Period')
#     ], string='Period Type', default='monthly', required=True)
#     date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
#     date_end = fields.Date(string='End Date', required=True)
#     achieved_leads = fields.Integer(string='Achieved Leads', compute='_compute_achieved_leads', store=False)
#     achievement_percentage = fields.Float(string='Achievement %', compute='_compute_achievement_percentage', store=False)
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('active', 'Active'),
#         ('completed', 'Completed')
#     ], string='Status', default='draft')
    
#     @api.depends('user_id', 'period_type', 'date_start')
#     def _compute_name(self):
#         for record in self:
#             if record.user_id and record.period_type:
#                 period_name = dict(record._fields['period_type'].selection).get(record.period_type)
#                 record.name = f"{record.user_id.name} - {period_name} Target"
#             else:
#                 record.name = "New Target"
    
#     @api.onchange('period_type', 'date_start')
#     def _onchange_period_type(self):
#         if self.date_start and self.period_type:
#             start_date = fields.Date.from_string(self.date_start)
#             if self.period_type == 'monthly':
#                 # Last day of the month using relativedelta
#                 end_date = start_date + relativedelta(months=1, days=-1)
#                 self.date_end = end_date
#             elif self.period_type == 'quarterly':
#                 # 3 months from start (last day of 3rd month)
#                 end_date = start_date + relativedelta(months=3, days=-1)
#                 self.date_end = end_date
#             elif self.period_type == 'yearly':
#                 # 1 year from start (last day of 12th month)
#                 end_date = start_date + relativedelta(years=1, days=-1)
#                 self.date_end = end_date
    
#     def _compute_achieved_leads(self):
#         for record in self:
#             # Find the "Sale Closed" stage
#             won_stage = self.env['crm.stage'].search([('name', '=', 'Sale Closed')], limit=1)
            
#             if won_stage:
#                 domain = [
#                     ('user_id', '=', record.user_id.id),
#                     ('stage_id', '=', won_stage.id),
#                     ('date_closed', '>=', fields.Datetime.to_datetime(record.date_start)),
#                     ('date_closed', '<=', fields.Datetime.to_datetime(record.date_end).replace(hour=23, minute=59, second=59))
#                 ]
#             else:
#                 # Fallback: if "Sale Closed" stage not found, use is_won field
#                 domain = [
#                     ('user_id', '=', record.user_id.id),
#                     ('probability', '=', 100),  # Won leads have 100% probability
#                     ('date_closed', '>=', fields.Datetime.to_datetime(record.date_start)),
#                     ('date_closed', '<=', fields.Datetime.to_datetime(record.date_end).replace(hour=23, minute=59, second=59))
#                 ]
            
#             record.achieved_leads = self.env['crm.lead'].search_count(domain)
    
#     @api.depends('achieved_leads', 'target_leads')
#     def _compute_achievement_percentage(self):
#         for record in self:
#             if record.target_leads > 0:
#                 record.achievement_percentage = (record.achieved_leads / record.target_leads) * 100
#             else:
#                 record.achievement_percentage = 0.0
    
#     def action_activate(self):
#         self.write({'state': 'active'})
    
#     def action_complete(self):
#         self.write({'state': 'completed'})
    
#     def action_view_leads(self):
#         """Open the list of leads for this target period"""
#         self.ensure_one()
        
#         # Find the "Sale Closed" stage
#         won_stage = self.env['crm.stage'].search([('name', '=', 'Sale Closed')], limit=1)
        
#         if won_stage:
#             domain = [
#                 ('user_id', '=', self.user_id.id),
#                 ('stage_id', '=', won_stage.id),
#                 ('date_closed', '>=', fields.Datetime.to_datetime(self.date_start)),
#                 ('date_closed', '<=', fields.Datetime.to_datetime(self.date_end).replace(hour=23, minute=59, second=59))
#             ]
#         else:
#             # Fallback
#             domain = [
#                 ('user_id', '=', self.user_id.id),
#                 ('probability', '=', 100),
#                 ('date_closed', '>=', fields.Datetime.to_datetime(self.date_start)),
#                 ('date_closed', '<=', fields.Datetime.to_datetime(self.date_end).replace(hour=23, minute=59, second=59))
#             ]
        
#         return {
#             'name': f'Won Leads for {self.user_id.name}',
#             'type': 'ir.actions.act_window',
#             'res_model': 'crm.lead',
#             'view_mode': 'list,form,kanban',
#             'domain': domain,
#             'context': {'default_user_id': self.user_id.id}
        # }


# 1st working code

# from odoo import models, fields, api
# from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta


# class CrmLeadTarget(models.Model):
#     _name = 'crm.lead.target'
#     _description = 'Individual Lead Target'
#     _order = 'date_start desc'

#     name = fields.Char(string='Target Name', compute='_compute_name', store=True)
#     user_id = fields.Many2one('res.users', string='Salesperson', required=True, ondelete='cascade')
#     target_leads = fields.Integer(string='Target Leads', required=True, default=0)
#     period_type = fields.Selection([
#         ('monthly', 'Monthly'),
#         ('quarterly', 'Quarterly'),
#         ('yearly', 'Yearly'),
#         ('custom', 'Custom Period')
#     ], string='Period Type', default='monthly', required=True)
#     date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
#     date_end = fields.Date(string='End Date', required=True)
#     achieved_leads = fields.Integer(string='Achieved Leads', compute='_compute_achieved_leads', store=False)
#     achievement_percentage = fields.Float(string='Achievement %', compute='_compute_achievement_percentage', store=False)
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('active', 'Active'),
#         ('completed', 'Completed')
#     ], string='Status', default='draft')
    
#     @api.depends('user_id', 'period_type', 'date_start')
#     def _compute_name(self):
#         for record in self:
#             if record.user_id and record.period_type:
#                 period_name = dict(record._fields['period_type'].selection).get(record.period_type)
#                 record.name = f"{record.user_id.name} - {period_name} Target"
#             else:
#                 record.name = "New Target"
    
#     @api.onchange('period_type', 'date_start')
#     def _onchange_period_type(self):
#         if self.date_start and self.period_type:
#             start_date = fields.Date.from_string(self.date_start)
#             if self.period_type == 'monthly':
#                 # Last day of the month using relativedelta
#                 end_date = start_date + relativedelta(months=1, days=-1)
#                 self.date_end = end_date
#             elif self.period_type == 'quarterly':
#                 # 3 months from start (last day of 3rd month)
#                 end_date = start_date + relativedelta(months=3, days=-1)
#                 self.date_end = end_date
#             elif self.period_type == 'yearly':
#                 # 1 year from start (last day of 12th month)
#                 end_date = start_date + relativedelta(years=1, days=-1)
#                 self.date_end = end_date
    
#     def _compute_achieved_leads(self):
#         for record in self:
#             domain = [
#                 ('user_id', '=', record.user_id.id),
#                 ('create_date', '>=', fields.Datetime.to_datetime(record.date_start)),
#                 ('create_date', '<=', fields.Datetime.to_datetime(record.date_end).replace(hour=23, minute=59, second=59))
#             ]
#             record.achieved_leads = self.env['crm.lead'].search_count(domain)
    
#     @api.depends('achieved_leads', 'target_leads')
#     def _compute_achievement_percentage(self):
#         for record in self:
#             if record.target_leads > 0:
#                 record.achievement_percentage = (record.achieved_leads / record.target_leads) * 100
#             else:
#                 record.achievement_percentage = 0.0
    
#     def action_activate(self):
#         self.write({'state': 'active'})
    
#     def action_complete(self):
#         self.write({'state': 'completed'})
    
#     def action_view_leads(self):
#         """Open the list of leads for this target period"""
#         self.ensure_one()
#         return {
#             'name': f'Leads for {self.user_id.name}',
#             'type': 'ir.actions.act_window',
#             'res_model': 'crm.lead',
#             'view_mode': 'list,form,kanban',
#             'domain': [
#                 ('user_id', '=', self.user_id.id),
#                 ('create_date', '>=', fields.Datetime.to_datetime(self.date_start)),
#                 ('create_date', '<=', fields.Datetime.to_datetime(self.date_end).replace(hour=23, minute=59, second=59))
#             ],
#             'context': {'default_user_id': self.user_id.id}
#         }