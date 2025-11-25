from odoo import models, fields, api
from datetime import datetime


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
                # Last day of the month
                if start_date.month == 12:
                    end_date = start_date.replace(day=31)
                else:
                    next_month = start_date.replace(month=start_date.month + 1, day=1)
                    end_date = next_month.replace(day=1) - fields.Datetime.timedelta(days=1)
                self.date_end = end_date
            elif self.period_type == 'quarterly':
                # 3 months from start
                month = start_date.month + 2
                year = start_date.year
                if month > 12:
                    month -= 12
                    year += 1
                end_date = start_date.replace(year=year, month=month)
                # Last day of that month
                if month == 12:
                    end_date = end_date.replace(day=31)
                else:
                    next_month = end_date.replace(month=end_date.month + 1, day=1)
                    end_date = next_month - fields.Datetime.timedelta(days=1)
                self.date_end = end_date
            elif self.period_type == 'yearly':
                # 1 year from start
                self.date_end = start_date.replace(year=start_date.year + 1) - fields.Datetime.timedelta(days=1)
    
    def _compute_achieved_leads(self):
        for record in self:
            domain = [
                ('user_id', '=', record.user_id.id),
                ('create_date', '>=', fields.Datetime.to_datetime(record.date_start)),
                ('create_date', '<=', fields.Datetime.to_datetime(record.date_end).replace(hour=23, minute=59, second=59))
            ]
            record.achieved_leads = self.env['crm.lead'].search_count(domain)
    
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
    
    def action_view_leads(self):
        """Open the list of leads for this target period"""
        self.ensure_one()
        return {
            'name': f'Leads for {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,form,kanban',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('create_date', '>=', fields.Datetime.to_datetime(self.date_start)),
                ('create_date', '<=', fields.Datetime.to_datetime(self.date_end).replace(hour=23, minute=59, second=59))
            ],
            'context': {'default_user_id': self.user_id.id}
        }