from odoo import models, fields, api

class AssignLeadsWizard(models.TransientModel):
    _name = 'assign.leads.wizard'
    _description = 'Assign Leads to User Wizard'

    user_id = fields.Many2one(
        'res.users',
        string='Assign To',
        required=True,
        domain=[('share', '=', False)],  # Only internal users
        help='Select the user to assign the selected leads'
    )
    
    lead_ids = fields.Many2many(
        'crm.lead',
        string='Leads',
        help='Selected leads to be assigned'
    )
    
    lead_count = fields.Integer(
        string='Number of Leads',
        compute='_compute_lead_count',
        store=False
    )
    
    @api.depends('lead_ids')
    def _compute_lead_count(self):
        for wizard in self:
            wizard.lead_count = len(wizard.lead_ids)
    
    @api.model
    def default_get(self, fields_list):
        """Override to get active_ids from context"""
        res = super(AssignLeadsWizard, self).default_get(fields_list)
        
        # Get selected lead IDs from context
        active_ids = self.env.context.get('active_ids', [])
        
        if active_ids and 'lead_ids' in fields_list:
            res['lead_ids'] = [(6, 0, active_ids)]
        
        return res
    
    def action_assign_leads(self):
        """Assign selected leads to the chosen user"""
        self.ensure_one()
        
        if self.lead_ids and self.user_id:
            # Assign all selected leads to the user
            self.lead_ids.write({
                'user_id': self.user_id.id,
            })
            
            # Optional: Add a message to the leads' chatter
            for lead in self.lead_ids:
                lead.message_post(
                    body=f"Lead assigned to {self.user_id.name} by {self.env.user.name}",
                    message_type='notification'
                )
        
        return {'type': 'ir.actions.act_window_close'}