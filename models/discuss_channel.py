from odoo import models, api, _
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'
    
    @api.model
    def channel_get(self, partners_to):
        """
        Override to prevent agents from creating chat with other agents.
        Admins are exempt from this restriction.
        """
        try:
            # Reference to our Sales/Agents group
            agents_group = self.env.ref('restrict_agent_chat.group_sales_agents', raise_if_not_found=False)
            
            if not agents_group:
                _logger.warning("Agents group not found. Chat restriction not applied.")
                return super(DiscussChannel, self).channel_get(partners_to)
            
            current_user = self.env.user
            is_admin = current_user.has_group('base.group_system')
            
            if is_admin:
                return super(DiscussChannel, self).channel_get(partners_to)
            
            is_current_user_agent = agents_group in current_user.groups_id
            
            if is_current_user_agent:
                target_partners = self.env['res.partner'].browse(partners_to)
                target_users = target_partners.mapped('user_ids').filtered(lambda u: u.active)
                
                for user in target_users:
                    if user.has_group('base.group_system'):
                        continue
                    
                    if agents_group in user.groups_id:
                        raise AccessError(_(
                            "You cannot start a chat with %s. "
                            "Agents are not allowed to chat with other agents. "
                            "Please contact an administrator if you need to communicate."
                        ) % user.name)
            
        except Exception as e:
            _logger.error("Error in channel_get restriction: %s", str(e))
            if isinstance(e, AccessError):
                raise
        
        return super(DiscussChannel, self).channel_get(partners_to)
    
    def _notify_thread(self, message, msg_vals=False, **kwargs):
        """
        Additional check when sending messages to existing channels
        """
        try:
            agents_group = self.env.ref('restrict_agent_chat.group_sales_agents', raise_if_not_found=False)
            
            if agents_group:
                current_user = self.env.user
                is_admin = current_user.has_group('base.group_system')
                
                if not is_admin and agents_group in current_user.groups_id:
                    for channel in self:
                        if channel.channel_type == 'chat':
                            other_members = channel.channel_member_ids.filtered(
                                lambda m: m.partner_id != current_user.partner_id
                            )
                            
                            for member in other_members:
                                member_user = member.partner_id.user_ids.filtered(lambda u: u.active)
                                if member_user and not member_user.has_group('base.group_system'):
                                    if agents_group in member_user.groups_id:
                                        raise AccessError(_(
                                            "You cannot send messages to %s. "
                                            "Agents are not allowed to chat with other agents."
                                        ) % member.partner_id.name)
        except Exception as e:
            _logger.error("Error in _notify_thread restriction: %s", str(e))
            if isinstance(e, AccessError):
                raise
        
        return super(DiscussChannel, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)