# from odoo import models, fields

# class ResUsers(models.Model):
#     _inherit = 'res.users'

#     vicidial_extension = fields.Char("Vicidial Extension")
import logging
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied
from odoo.http import request
import ipaddress

_logger = logging.getLogger(__name__)



class ResUsers(models.Model):
    _inherit = 'res.users'
    vicidial_extension = fields.Char("Vicidial Extension")
    
    allowed_ips = fields.Text(
        string='Allowed IP Addresses',
        help='Enter allowed IP addresses (one per line or comma-separated).\n'
             'Supports individual IPs (e.g., 192.168.1.100) or CIDR notation (e.g., 192.168.1.0/24).\n'
             'Leave empty to allow login from any IP address.'
    )
    
    ip_restriction_enabled = fields.Boolean(
        string='Enable IP Restriction',
        default=False,
        help='Enable IP address restriction for this user'
    )
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

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("****CREATE METHOD CALLED****")
        # Handle password before creating user
        for vals in vals_list:
            pwd = vals.get("x_studio_password")
            if pwd:
                _logger.info("Setting password from x_studio_password: %s", pwd)
                vals['password'] = pwd
                # DON'T pop x_studio_password - let it save to the field
            
        users = super().create(vals_list)
        return users

    def write(self, vals):
        _logger.info("****WRITE METHOD CALLED****")
        _logger.info("Current user IDs: %s", self.ids)
        
        # Handle password field - but don't remove x_studio_password from vals
        pwd = vals.get("x_studio_password")
        if pwd:
            vals['password'] = pwd
            # DON'T pop x_studio_password - let it save to the field
            
        res = super().write(vals)
        _logger.info("Write result: %s", res)
        return res                               

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

    @classmethod
    def authenticate(cls, db, credential, user_agent_env):
        """Override authenticate to add IP restriction check"""
        # First perform normal authentication
        auth_info = super(ResUsers, cls).authenticate(db, credential, user_agent_env)
        
        # If authentication successful and we have a request context, check IP
        if auth_info and request:
            uid = auth_info.get('uid')
            if uid:
                with cls.pool.cursor() as cr:
                    env = api.Environment(cr, uid, {})
                    user = env['res.users'].browse(uid)
                    if user.exists():
                        user._check_ip_restriction()
        
        return auth_info
    
    def _check_ip_restriction(self):
        """Check if the current IP is allowed for this user"""
        # Only check if IP restriction is enabled and IPs are configured
        if not self.ip_restriction_enabled or not self.allowed_ips:
            return True
        
        # Make sure we have a request object
        if not request:
            _logger.warning('No request object available for IP check for user %s', self.login)
            return True
        
        # Get client IP address
        client_ip = None
        # Try to get real IP from headers (in case of proxy)
        client_ip = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR')
        if client_ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            client_ip = client_ip.split(',')[0].strip()
        else:
            client_ip = request.httprequest.environ.get('REMOTE_ADDR')
        
        if not client_ip:
            _logger.error('Could not determine client IP address')
            raise AccessDenied(_('Could not determine your IP address'))
        
        # Parse allowed IPs (support both comma and newline separated)
        allowed_ips_list = []
        for ip in self.allowed_ips.replace(',', '\n').split('\n'):
            ip = ip.strip()
            if ip:
                allowed_ips_list.append(ip)
        
        # Check if client IP is in allowed list
        is_allowed = self._is_ip_allowed(client_ip, allowed_ips_list)
        
        if not is_allowed:
            _logger.warning(
                'Access denied for user "%s" (ID: %s) from IP %s. Allowed IPs: %s',
                self.login, self.id, client_ip, ', '.join(allowed_ips_list)
            )
            raise AccessDenied(
                _('Access denied: Your IP address (%s) is not authorized to access this account. '
                'Please contact the system administrator for assistance.') % client_ip
            )

        
        _logger.info('User "%s" logged in successfully from IP %s', self.login, client_ip)
        return True
    
    def _is_ip_allowed(self, client_ip, allowed_ips_list):
        """
        Check if client IP is in the allowed list.
        Supports both individual IPs and CIDR notation.
        """
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            
            for allowed_ip in allowed_ips_list:
                try:
                    # Check if it's a CIDR notation (network range)
                    if '/' in allowed_ip:
                        network = ipaddress.ip_network(allowed_ip, strict=False)
                        if client_ip_obj in network:
                            return True
                    else:
                        # Individual IP comparison
                        if client_ip == allowed_ip:
                            return True
                except ValueError as e:
                    _logger.warning('Invalid IP/Network format: %s - %s', allowed_ip, str(e))
                    continue
            
            return False
        except ValueError as e:
            _logger.error('Invalid client IP address: %s - %s', client_ip, str(e))
            return False 
