from odoo import models, fields, api
import base64
import io
import xlsxwriter
from datetime import datetime
from odoo.exceptions import UserError
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class ExportLeadWizard(models.TransientModel):
    # _inherit = 'crm.lead'
    _name = 'export.lead.wizard'
    _description = 'Export Leads Wizard'
    available_field_ids = fields.Many2many(
        'ir.model.fields',
        'export_wizard_available_fields_rel',
        'wizard_id',
        'field_id',
        string="Available Fields",
        compute='_compute_available_fields',
        store=False
    )
    
    export_fields = fields.Many2many(
        "ir.model.fields",
        'export_wizard_selected_fields_rel',
        'wizard_id',
        'field_id',
        string="Fields to Export",
        help="Select fields to export",
    )

    FORM_FIELDS_MAP = {
        "credit_card": [
                "amex_date", "amex_center", "amex_company_name", "amex_abn",
                "amex_address_1", "amex_address_2", "amex_suburb", "amex_state",
                "amex_country", "amex_business_website", "amex_saluation",
                "amex_first_name", "amex_last_name", "amex_position", "amex_contact",
                "amex_email", "amex_current_turnover", "amex_estimated_expense",
                "amex_existing_product", "amex_additional_info", "amex_tool_used"
            ],
        "first_energy": [   
                "internal_dnc_checked", "existing_sale", "online_enquiry_form", "vendor_id",
                "agent", "channel_ref", "sale_ref", "lead_ref", "incentive", "sale_date",
                "campaign_ref", "promo_code", "current_elec_retailer", "current_gas_retailer",
                "multisite", "existing_customer", "customer_account_no", "customer_type",
                "account_name", "abn", "acn", "business_name", "trustee_name", "trading_name",
                "position", "sale_type", "customer_title", "first_name", "last_name",
                "phone_landline", "phone_mobile", "auth_date_of_birth", "auth_expiry",
                "auth_no", "auth_type", "email", "life_support", "concessioner_number",
                "concession_expiry", "concession_flag", "concession_start_date",
                "concession_type", "conc_first_name", "conc_last_name", "secondary_title",
                "sec_first_name", "sec_last_name", "sec_auth_date_of_birth", "sec_auth_no",
                "sec_auth_type", "sec_auth_expiry", "sec_email", "sec_phone_home",
                "sec_mobile_number", "site_apartment_no", "site_apartment_type",
                "site_building_name", "site_floor_no", "site_floor_type",
                "site_location_description", "site_lot_number", "site_street_number",
                "site_street_name", "site_street_number_suffix", "site_street_type",
                "site_street_suffix", "site_suburb", "site_state", "site_post_code",
                "gas_site_apartment_number", "gas_site_apartment_type",
                "gas_site_building_name", "gas_site_floor_number", "gas_site_floor_type",
                "gas_site_location_description", "gas_site_lot_number", "gas_site_street_name",
                "gas_site_street_number", "gas_site_street_number_suffix",
                "gas_site_street_type", "gas_site_street_suffix", "gas_site_suburb",
                "gas_site_state", "gas_site_post_code", "network_tariff_code", "nmi", "mirn",
                "fuel", "feed_in", "annual_usage", "gas_annual_usage", "product_code",
                "gas_product_code", "offer_description", "gas_offer_description",
                "green_percent", "proposed_transfer_date", "gas_proposed_transfer_date",
                "bill_cycle_code", "gas_bill_cycle_code", "average_monthly_spend", "is_owner",
                "has_accepted_marketing", "email_account_notice", "email_invoice",
                "billing_email", "postal_building_name", "postal_apartment_number",
                "postal_apartment_type", "postal_floor_number", "postal_floor_type",
                "postal_lot_no", "postal_street_number", "postal_street_number_suffix",
                "postal_street_name", "postal_street_type", "postal_street_suffix",
                "postal_suburb", "postal_post_code", "postal_state", "comments",
                "transfer_special_instructions", "medical_cooling",
                "medical_cooling_energy_rebate", "benefit_end_date", "sales_class",
                "bill_group_code", "gas_meter_number", "centre_name", "qc_name",
                "verifiers_name", "tl_name", "dnc_ref_no", "audit_2", "welcome_call"
            ],
        "dodo_power": [
                "dp_internal_dnc_checked", "dp_existing_sale", "dp_online_enquiry_form",
                "dp_sales_name", "dp_sales_reference", "dp_agreement_date",
                "dp_site_address_postcode", "dp_site_addr_unit_type", "dp_site_addr_unit_no",
                "dp_site_addr_floor_type", "dp_site_addr_floor_no", "dp_site_addr_street_no",
                "dp_site_addr_street_no_suffix", "dp_site_addr_street_name", "dp_site_addr_street_type",
                "dp_site_addr_suburb", "dp_site_addr_state", "dp_site_addr_postcode", "dp_site_addr_desc",
                "dp_site_access", "dp_site_more_than_12_months", "dp_prev_addr_1", "dp_prev_addr_2",
                "dp_prev_addr_state", "dp_prev_addr_postcode", "dp_billing_address", "dp_bill_addr_1",
                "dp_bill_addr_2", "dp_bill_addr_state", "dp_bill_addr_postcode", "dp_concession",
                "dp_concession_card_type", "dp_concession_card_no", "dp_concession_start_date",
                "dp_concession_exp_date", "dp_concession_first_name", "dp_concession_middle_name",
                "dp_concession_last_name", "dp_product_code", "dp_meter_type", "dp_kwh_usage_per_day",
                "dp_how_many_people", "dp_how_many_bedrooms", "dp_solar_power", "dp_solar_type",
                "dp_solar_output", "dp_green_energy", "dp_winter_gas_usage", "dp_summer_gas_usage",
                "dp_monthly_winter_spend", "dp_monthly_summer_spend", "dp_invoice_method",
                "dp_customer_salutation", "dp_first_name", "dp_last_name", "dp_date_of_birth",
                "dp_email_contact", "dp_contact_number", "dp_hearing_impaired", "dp_secondary_contact",
                "dp_secondary_salutation", "dp_secondary_first_name", "dp_secondary_last_name",
                "dp_secondary_date_of_birth", "dp_secondary_email", "dp_referral_code", "dp_new_username",
                "dp_new_password", "dp_customer_dlicense", "dp_customer_dlicense_state",
                "dp_customer_dlicense_exp", "dp_customer_passport", "dp_customer_passport_exp",
                "dp_customer_medicare", "dp_customer_medicare_ref", "dp_position_at_current_employer",
                "dp_employment_status", "dp_current_employer", "dp_employer_contact_number",
                "dp_years_in_employment", "dp_months_in_employment", "dp_employment_confirmation",
                "dp_life_support", "dp_life_support_machine_type", "dp_life_support_details", "dp_nmi",
                "dp_nmi_source", "dp_mirn", "dp_mirn_source", "dp_connection_date",
                "dp_electricity_connection", "dp_gas_connection", "dp_12_month_disconnection",
                "dp_cert_electrical_safety", "dp_cert_electrical_safety_id",
                "dp_cert_electrical_safety_sent", "dp_explicit_informed_consent", "dp_center_name",
                "dp_closer_name", "dp_dnc_wash_number", "dp_dnc_exp_date", "dp_audit_1", "dp_audit_2",
                "dp_welcome_call"
            ],
        "momentum":[
                "momentum_energy_transaction_reference","momentum_energy_transaction_channel","momentum_energy_transaction_date",
                "momentum_energy_transaction_verification_code","momentum_energy_transaction_source","momentum_energy_customer_type",
                "momentum_energy_customer_sub_type","momentum_energy_communication_preference","momentum_energy_promotion_allowed",
                "momentum_energy_passport_id","momentum_energy_passport_expiry","momentum_energy_passport_country",
                "momentum_energy_driving_license_id","momentum_energy_driving_license_expiry","momentum_energy_driving_license_state",
                "momentum_energy_medicare_id","momentum_energy_medicare_number","momentum_energy_medicare_expiry",
                "momentum_energy_industry","momentum_energy_entity_name","momentum_energy_trading_name","momentum_energy_trustee_name",
                "momentum_energy_abn_document_id","momentum_energy_acn_document_id","momentum_energy_primary_contact_type",
                "momentum_energy_primary_salutation","momentum_energy_primary_first_name","momentum_energy_primary_middle_name",
                "momentum_energy_primary_last_name","momentum_energy_primary_country_of_birth","momentum_energy_primary_date_of_birth",
                "momentum_energy_primary_email","momentum_energy_primary_address_type","momentum_energy_primary_street_number",
                "momentum_energy_primary_street_name","momentum_energy_primary_unit_number","momentum_energy_primary_suburb",
                "momentum_energy_primary_state","momentum_energy_primary_post_code","momentum_energy_primary_phone_work",
                "momentum_energy_primary_phone_home","momentum_energy_primary_phone_mobile","momentum_energy_secondary_contact_type",
                "momentum_energy_secondary_salutation","momentum_energy_secondary_first_name","momentum_energy_secondary_middle_name",
                "momentum_energy_secondary_last_name","momentum_energy_secondary_country_of_birth","momentum_energy_secondary_date_of_birth",
                "momentum_energy_secondary_email","momentum_energy_secondary_address_type","momentum_energy_secondary_street_number",
                "momentum_energy_secondary_street_name","momentum_energy_secondary_unit_number","momentum_energy_secondary_suburb",
                "momentum_energy_secondary_state","momentum_energy_secondary_post_code","momentum_energy_secondary_phone_work",
                "momentum_energy_secondary_phone_home","momentum_energy_secondary_phone_mobile","momentum_energy_service_type",
                "momentum_energy_service_sub_type","momentum_energy_service_connection_id","momentum_energy_service_meter_id",
                "momentum_energy_service_start_date","momentum_energy_estimated_annual_kwhs","momentum_energy_lot_number",
                "momentum_energy_service_name","momentum_energy_property_name","momentum_energy_unit_type",
                "momentum_energy_unit_number","momentum_energy_floor_type","momentum_energy_floor_number","momentum_energy_street_number_suffix",
                "momentum_energy_street_name_suffix","momentum_energy_service_street_number",
                "momentum_energy_service_street_name","momentum_energy_service_street_type_code","momentum_energy_service_suburb",
                "momentum_energy_service_state","momentum_energy_service_post_code","momentum_energy_service_access_instructions",
                "momentum_energy_service_safety_instructions","momentum_energy_offer_quote_date","momentum_energy_service_offer_code",
                "momentum_energy_owr","momentum_energy_service_plan_code","momentum_energy_contract_term_code",
                "momentum_energy_contract_date","momentum_energy_payment_method","momentum_energy_bill_cycle_code",
                "momentum_energy_bill_delivery_method","momentum_energy_concession","momentum_energy_concession_obtained",
                "momentum_energy_conc_has_ms","momentum_energy_conc_in_grp_home","momentum_energy_conc_start_date",
                "momentum_energy_conc_end_date","momentum_energy_conc_card_type_code","momentum_energy_conc_card_code",
                "momentum_energy_conc_card_number","momentum_energy_conc_card_exp_date","momentum_energy_card_first_name",
                "momentum_energy_card_last_name","momentum_transaction_id"
            ],
        
        "optus_nbn":[
                "optus_date", "optus_activation", "optus_order", "optus_customer",
                "optus_address", "optus_service", "optus_plan", "optus_per_month",
                "optus_center", "optus_salesperson", "optus_contact", "optus_email",
                "optus_notes", "optus_dcn", "optus_audit_1", "optus_audit_2"
            ],
        "dodo_nbn":[
                "do_nbn_receipt", "do_nbn_service", "do_nbn_plans", "do_nbn_current",
                "do_nbn_current_no", "do_nbn_title", "do_first_name", "do_last_name",
                "do_mobile_no", "do_installation_address", "do_house_number",
                "do_street_name", "do_street_type", "do_suburb", "do_state",
                "do_post_code", "do_sale_date", "do_center_name", "do_closer_name",
                "do_dnc_ref_no", "do_dnc_exp_date", "do_audit_1", "do_audit_2"
            ],
        "home_moving":[
                "hm_moving_date", "hm_address", "hm_property_type", "hm_ownership",
                "hm_status", "hm_first_name", "hm_last_name", "hm_job_title", "hm_dob",
                "hm_friend_code", "hm_mobile", "hm_work_phone", "hm_home_phone",
                "hm_email", "hm_how_heard", "hm_agency_name", "hm_broker_name",
                "hm_agency_contact_number", "hm_connect_electricity", "hm_connect_gas",
                "hm_connect_internet", "hm_connect_water", "hm_connect_tv",
                "hm_connect_removalist", "hm_accept_terms"
            ],
        "business_loan":[
                "bs_amount_to_borrow", "bs_business_name", "bs_trading_duration",
                "bs_monthly_turnover", "bs_first_name", "bs_last_name",
                "bs_email", "bs_home_owner", "bs_accept_terms"
            ],
        "home_loan":[
                "hl_user_want_to", "hl_expected_price", "hl_deposit_amount",
                "hl_buying_reason", "hl_first_home_buyer", "hl_property_type",
                "hl_property_usage", "hl_credit_history", "hl_income_source",
                "hl_first_name", "hl_last_name", "hl_contact", "hl_email",
                "hl_accept_terms"
            ],
        "insurance":[
                "hi_current_address", "hi_cover_type", "hi_have_insurance_cover",
                "hi_insurance_considerations", "hi_dob", "hi_annual_taxable_income",
                "hi_full_name", "hi_contact_number", "hi_email"
            ],
        "veu":[
                "u_first_name", "u_last_name", "u_mobile_no", "u_email",
                "u_post_code", "u_interested_in", "u_how", "u_accept_terms"
            ]        

        # Add others…
    }


    form_type = fields.Selection([
    ('credit_card', 'Credit Card Sales'),
    ('first_energy', '1st Energy Sales Form'),
    ('momentum', 'Momentum Sales Form'),
    ('dodo_power', 'Dodo Power and Gas Sales Form'),
    ('optus_nbn', 'Optus NBN Sales Form'),
    ('dodo_nbn', 'Dodo NBN Sales Form'),
    ('home_moving', 'Home Moving'),
    ('business_loan', 'Business Loan'),
    ("home_loan", "Home Loan"),
    ("insurance", "Health Insurance"),
    ("veu", "Victorian Energy")
    ], string="Select Form Type", required=True)

    @api.depends('form_type')
    def _compute_available_fields(self):
        """Compute available fields based on form type"""
        for wizard in self:
            if wizard.form_type:
                allowed_fields = self.FORM_FIELDS_MAP.get(wizard.form_type, [])
                if allowed_fields:
                    fields_records = self.env['ir.model.fields'].search([
                        ("model", "=", "crm.lead"),
                        ("name", "in", allowed_fields)
                    ])
                    wizard.available_field_ids = fields_records
                else:
                    wizard.available_field_ids = False
            else:
                wizard.available_field_ids = False

    @api.onchange("form_type")
    def _onchange_form_type(self):
        """Filter available fields based on selected form type"""
        result = {}
        
        # Clear existing selections
        self.export_fields = [(5, 0, 0)]
        
        if not self.form_type:
            return {
                "domain": {
                    "export_fields": [("id", "=", False)]
                }
            }

        allowed_fields = self.FORM_FIELDS_MAP.get(self.form_type, [])
        
        if allowed_fields:
            # Check if fields exist in database
            existing_fields = self.env['ir.model.fields'].search([
                ("model", "=", "crm.lead"), 
                ("name", "in", allowed_fields)
            ])
            
            if not existing_fields:
                result['warning'] = {
                    'title': 'No Fields Found',
                    'message': f'No fields found for {self.form_type}. Please check if custom fields are installed.'
                }
                domain = [("id", "=", False)]
            else:
                domain = [
                    ("model", "=", "crm.lead"), 
                    ("name", "in", allowed_fields)
                ]
        else:
            domain = [("id", "=", False)]
        
        result['domain'] = {"export_fields": domain}
        return result


    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    file_data = fields.Binary('File', readonly=True)
    file_name = fields.Char('File Name')

    def action_export(self):
        """Export selected fields to Excel"""
        # Build domain for lead search
        domain = []
        if self.start_date:
            domain.append(('create_date', '>=', self.start_date))
        if self.end_date:
            domain.append(('create_date', '<=', self.end_date))

        # Get selected field names
        selected_field_names = self.export_fields.mapped("name")

        if not selected_field_names:
            raise UserError("Please select at least one field to export.")

        # Search for leads
        leads = self.env['crm.lead'].search(domain)

        if not leads:
            raise UserError("No leads found for the selected date range.")

        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Leads')

        # Formats
        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#DCE6F1',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        text_fmt = workbook.add_format({
            'text_wrap': True,
            'border': 1,
            'valign': 'top'
        })
        title_fmt = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center'
        })

        # Set column widths
        worksheet.set_column(0, len(selected_field_names) - 1, 20)

        # Title
        form_type_display = self.form_type.replace('_', ' ').title() if self.form_type else 'Leads'
        worksheet.merge_range(0, 0, 0, len(selected_field_names) - 1,
                            f"Lead Export - {form_type_display}",
                            title_fmt)

        # Write headers
        for col_idx, field_name in enumerate(selected_field_names):
            field_obj = self.export_fields.filtered(lambda f: f.name == field_name)
            display_name = field_obj.field_description if field_obj else field_name
            worksheet.write(1, col_idx, display_name, header_fmt)

        # Write data rows
        for row_idx, lead in enumerate(leads, 2):
            for col_idx, field_name in enumerate(selected_field_names):
                value = self._get_field_value(lead, field_name)
                worksheet.write(row_idx, col_idx, value, text_fmt)

        # Footer
        footer_text = f"Exported by {self.env.user.name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        worksheet.merge_range(len(leads) + 3, 0, len(leads) + 3, len(selected_field_names) - 1,
                            footer_text,
                            workbook.add_format({'italic': True, 'align': 'right'}))

        workbook.close()
        output.seek(0)
        file_data = output.read()

        # Create attachment
        file_name = f"{self.form_type}_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def _get_field_value(self, lead, field_name):
        """Get and format field value based on field type"""
        try:
            field_obj = lead._fields.get(field_name)
            if not field_obj:
                return ''

            value = getattr(lead, field_name, None)

            if not value and value != 0 and value is not False:
                return ''

            # Handle different field types
            if field_obj.type == 'many2one':
                return value.display_name if value else ''
            elif field_obj.type in ('many2many', 'one2many'):
                return ', '.join(rec.display_name for rec in value) if value else ''
            elif field_obj.type == 'selection':
                if value:
                    try:
                        selection_dict = dict(field_obj.selection) if not callable(field_obj.selection) else {}
                        return selection_dict.get(value, str(value))
                    except:
                        return str(value)
                return ''
            elif field_obj.type == 'boolean':
                return "Yes" if value else "No"
            elif field_obj.type in ('date', 'datetime'):
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                return str(value) if value else ''
            elif field_obj.type == 'monetary':
                return f"{value:.2f}" if value else '0.00'
            elif field_obj.type == 'float':
                return f"{value:.2f}" if value else '0.00'
            else:
                return str(value) if value else ''

        except Exception as e:
            _logger.warning(f"Error reading field {field_name}: {str(e)}")
            return ''

# working code

# from odoo import models, fields, api
# import base64
# import io
# import xlsxwriter
# from datetime import datetime
# from odoo.exceptions import UserError
# from lxml import etree
# import logging

# _logger = logging.getLogger(__name__)


# class ExportLeadWizard(models.TransientModel):
#     # _inherit = 'crm.lead'
#     _name = 'export.lead.wizard'
#     _description = 'Export Leads Wizard'

#     form_type = fields.Selection([
#         # ('amex', 'Amex Sales Form'),
#         ('credit_card', 'Credit Card Sales'),
#         ('first_energy', '1st Energy Sales Form'),
#         ('momentum', 'Momentum Sales Form'),
#         ('dodo_power', 'Dodo Power and Gas Sales Form'),
#         ('optus_nbn', 'Optus NBN Sales Form'),
#         ('dodo_nbn', 'Dodo NBN Sales Form'),
#         ('home_moving', 'Home Moving'),
#         ('business_loan', 'Business Loan'),
#         ("home_loan", "Home Loan"),
#         ("insurance", "Health Insurance"),
#         ("veu", "Victorian Energy")

#     ], string="Select Form Type", required=True)

#     start_date = fields.Date(string="Start Date")
#     end_date = fields.Date(string="End Date")

#     file_data = fields.Binary('File', readonly=True)
#     file_name = fields.Char('File Name')

#     def action_export(self):
#         domain = []
#         export_fields = []

#         if self.form_type == 'credit_card':
#             domain = [('lead_for', '=', 'credit_card_call_center')]
#             export_fields = [
#                 "amex_date", "amex_center", "amex_company_name", "amex_abn",
#                 "amex_address_1", "amex_address_2", "amex_suburb", "amex_state",
#                 "amex_country", "amex_business_website", "amex_saluation",
#                 "amex_first_name", "amex_last_name", "amex_position", "amex_contact",
#                 "amex_email", "amex_current_turnover", "amex_estimated_expense",
#                 "amex_existing_product", "amex_additional_info", "amex_tool_used"
#             ]

#         elif self.form_type == 'first_energy':
#             domain = [('lead_for', '=', 'energy_call_center'),('stage_2_campign_name', '=', 'first_energy')]
#             export_fields = [   
#                 "internal_dnc_checked", "existing_sale", "online_enquiry_form", "vendor_id",
#                 "agent", "channel_ref", "sale_ref", "lead_ref", "incentive", "sale_date",
#                 "campaign_ref", "promo_code", "current_elec_retailer", "current_gas_retailer",
#                 "multisite", "existing_customer", "customer_account_no", "customer_type",
#                 "account_name", "abn", "acn", "business_name", "trustee_name", "trading_name",
#                 "position", "sale_type", "customer_title", "first_name", "last_name",
#                 "phone_landline", "phone_mobile", "auth_date_of_birth", "auth_expiry",
#                 "auth_no", "auth_type", "email", "life_support", "concessioner_number",
#                 "concession_expiry", "concession_flag", "concession_start_date",
#                 "concession_type", "conc_first_name", "conc_last_name", "secondary_title",
#                 "sec_first_name", "sec_last_name", "sec_auth_date_of_birth", "sec_auth_no",
#                 "sec_auth_type", "sec_auth_expiry", "sec_email", "sec_phone_home",
#                 "sec_mobile_number", "site_apartment_no", "site_apartment_type",
#                 "site_building_name", "site_floor_no", "site_floor_type",
#                 "site_location_description", "site_lot_number", "site_street_number",
#                 "site_street_name", "site_street_number_suffix", "site_street_type",
#                 "site_street_suffix", "site_suburb", "site_state", "site_post_code",
#                 "gas_site_apartment_number", "gas_site_apartment_type",
#                 "gas_site_building_name", "gas_site_floor_number", "gas_site_floor_type",
#                 "gas_site_location_description", "gas_site_lot_number", "gas_site_street_name",
#                 "gas_site_street_number", "gas_site_street_number_suffix",
#                 "gas_site_street_type", "gas_site_street_suffix", "gas_site_suburb",
#                 "gas_site_state", "gas_site_post_code", "network_tariff_code", "nmi", "mirn",
#                 "fuel", "feed_in", "annual_usage", "gas_annual_usage", "product_code",
#                 "gas_product_code", "offer_description", "gas_offer_description",
#                 "green_percent", "proposed_transfer_date", "gas_proposed_transfer_date",
#                 "bill_cycle_code", "gas_bill_cycle_code", "average_monthly_spend", "is_owner",
#                 "has_accepted_marketing", "email_account_notice", "email_invoice",
#                 "billing_email", "postal_building_name", "postal_apartment_number",
#                 "postal_apartment_type", "postal_floor_number", "postal_floor_type",
#                 "postal_lot_no", "postal_street_number", "postal_street_number_suffix",
#                 "postal_street_name", "postal_street_type", "postal_street_suffix",
#                 "postal_suburb", "postal_post_code", "postal_state", "comments",
#                 "transfer_special_instructions", "medical_cooling",
#                 "medical_cooling_energy_rebate", "benefit_end_date", "sales_class",
#                 "bill_group_code", "gas_meter_number", "centre_name", "qc_name",
#                 "verifiers_name", "tl_name", "dnc_ref_no", "audit_2", "welcome_call"
#             ]

#         elif self.form_type == 'dodo_power':
#             domain = [('lead_for', '=', 'energy_call_center')]
#             export_fields = [
#                 "dp_internal_dnc_checked", "dp_existing_sale", "dp_online_enquiry_form",
#                 "dp_sales_name", "dp_sales_reference", "dp_agreement_date",
#                 "dp_site_address_postcode", "dp_site_addr_unit_type", "dp_site_addr_unit_no",
#                 "dp_site_addr_floor_type", "dp_site_addr_floor_no", "dp_site_addr_street_no",
#                 "dp_site_addr_street_no_suffix", "dp_site_addr_street_name", "dp_site_addr_street_type",
#                 "dp_site_addr_suburb", "dp_site_addr_state", "dp_site_addr_postcode", "dp_site_addr_desc",
#                 "dp_site_access", "dp_site_more_than_12_months", "dp_prev_addr_1", "dp_prev_addr_2",
#                 "dp_prev_addr_state", "dp_prev_addr_postcode", "dp_billing_address", "dp_bill_addr_1",
#                 "dp_bill_addr_2", "dp_bill_addr_state", "dp_bill_addr_postcode", "dp_concession",
#                 "dp_concession_card_type", "dp_concession_card_no", "dp_concession_start_date",
#                 "dp_concession_exp_date", "dp_concession_first_name", "dp_concession_middle_name",
#                 "dp_concession_last_name", "dp_product_code", "dp_meter_type", "dp_kwh_usage_per_day",
#                 "dp_how_many_people", "dp_how_many_bedrooms", "dp_solar_power", "dp_solar_type",
#                 "dp_solar_output", "dp_green_energy", "dp_winter_gas_usage", "dp_summer_gas_usage",
#                 "dp_monthly_winter_spend", "dp_monthly_summer_spend", "dp_invoice_method",
#                 "dp_customer_salutation", "dp_first_name", "dp_last_name", "dp_date_of_birth",
#                 "dp_email_contact", "dp_contact_number", "dp_hearing_impaired", "dp_secondary_contact",
#                 "dp_secondary_salutation", "dp_secondary_first_name", "dp_secondary_last_name",
#                 "dp_secondary_date_of_birth", "dp_secondary_email", "dp_referral_code", "dp_new_username",
#                 "dp_new_password", "dp_customer_dlicense", "dp_customer_dlicense_state",
#                 "dp_customer_dlicense_exp", "dp_customer_passport", "dp_customer_passport_exp",
#                 "dp_customer_medicare", "dp_customer_medicare_ref", "dp_position_at_current_employer",
#                 "dp_employment_status", "dp_current_employer", "dp_employer_contact_number",
#                 "dp_years_in_employment", "dp_months_in_employment", "dp_employment_confirmation",
#                 "dp_life_support", "dp_life_support_machine_type", "dp_life_support_details", "dp_nmi",
#                 "dp_nmi_source", "dp_mirn", "dp_mirn_source", "dp_connection_date",
#                 "dp_electricity_connection", "dp_gas_connection", "dp_12_month_disconnection",
#                 "dp_cert_electrical_safety", "dp_cert_electrical_safety_id",
#                 "dp_cert_electrical_safety_sent", "dp_explicit_informed_consent", "dp_center_name",
#                 "dp_closer_name", "dp_dnc_wash_number", "dp_dnc_exp_date", "dp_audit_1", "dp_audit_2",
#                 "dp_welcome_call"
#             ]

#         elif self.form_type == 'momentum':
#             domain = [('lead_for', '=', 'energy_call_center'),('stage_2_campign_name', '=', 'momentum')]
#             export_fields = [
#                 "momentum_energy_transaction_reference","momentum_energy_transaction_channel","momentum_energy_transaction_date",
#                 "momentum_energy_transaction_verification_code","momentum_energy_transaction_source","momentum_energy_customer_type",
#                 "momentum_energy_customer_sub_type","momentum_energy_communication_preference","momentum_energy_promotion_allowed",
#                 "momentum_energy_passport_id","momentum_energy_passport_expiry","momentum_energy_passport_country",
#                 "momentum_energy_driving_license_id","momentum_energy_driving_license_expiry","momentum_energy_driving_license_state",
#                 "momentum_energy_medicare_id","momentum_energy_medicare_number","momentum_energy_medicare_expiry",
#                 "momentum_energy_industry","momentum_energy_entity_name","momentum_energy_trading_name","momentum_energy_trustee_name",
#                 "momentum_energy_abn_document_id","momentum_energy_acn_document_id","momentum_energy_primary_contact_type",
#                 "momentum_energy_primary_salutation","momentum_energy_primary_first_name","momentum_energy_primary_middle_name",
#                 "momentum_energy_primary_last_name","momentum_energy_primary_country_of_birth","momentum_energy_primary_date_of_birth",
#                 "momentum_energy_primary_email","momentum_energy_primary_address_type","momentum_energy_primary_street_number",
#                 "momentum_energy_primary_street_name","momentum_energy_primary_unit_number","momentum_energy_primary_suburb",
#                 "momentum_energy_primary_state","momentum_energy_primary_post_code","momentum_energy_primary_phone_work",
#                 "momentum_energy_primary_phone_home","momentum_energy_primary_phone_mobile","momentum_energy_secondary_contact_type",
#                 "momentum_energy_secondary_salutation","momentum_energy_secondary_first_name","momentum_energy_secondary_middle_name",
#                 "momentum_energy_secondary_last_name","momentum_energy_secondary_country_of_birth","momentum_energy_secondary_date_of_birth",
#                 "momentum_energy_secondary_email","momentum_energy_secondary_address_type","momentum_energy_secondary_street_number",
#                 "momentum_energy_secondary_street_name","momentum_energy_secondary_unit_number","momentum_energy_secondary_suburb",
#                 "momentum_energy_secondary_state","momentum_energy_secondary_post_code","momentum_energy_secondary_phone_work",
#                 "momentum_energy_secondary_phone_home","momentum_energy_secondary_phone_mobile","momentum_energy_service_type",
#                 "momentum_energy_service_sub_type","momentum_energy_service_connection_id","momentum_energy_service_meter_id",
#                 "momentum_energy_service_start_date","momentum_energy_estimated_annual_kwhs","momentum_energy_lot_number",
#                 "momentum_energy_service_name","momentum_energy_property_name","momentum_energy_unit_type",
#                 "momentum_energy_unit_number","momentum_energy_floor_type","momentum_energy_floor_number","momentum_energy_street_number_suffix",
#                 "momentum_energy_street_name_suffix","momentum_energy_service_street_number",
#                 "momentum_energy_service_street_name","momentum_energy_service_street_type_code","momentum_energy_service_suburb",
#                 "momentum_energy_service_state","momentum_energy_service_post_code","momentum_energy_service_access_instructions",
#                 "momentum_energy_service_safety_instructions","momentum_energy_offer_quote_date","momentum_energy_service_offer_code",
#                 "momentum_energy_owr","momentum_energy_service_plan_code","momentum_energy_contract_term_code",
#                 "momentum_energy_contract_date","momentum_energy_payment_method","momentum_energy_bill_cycle_code",
#                 "momentum_energy_bill_delivery_method","momentum_energy_concession","momentum_energy_concession_obtained",
#                 "momentum_energy_conc_has_ms","momentum_energy_conc_in_grp_home","momentum_energy_conc_start_date",
#                 "momentum_energy_conc_end_date","momentum_energy_conc_card_type_code","momentum_energy_conc_card_code",
#                 "momentum_energy_conc_card_number","momentum_energy_conc_card_exp_date","momentum_energy_card_first_name",
#                 "momentum_energy_card_last_name","momentum_transaction_id"
#             ]


#         elif self.form_type == 'optus_nbn':
#             domain = [('lead_for', '=', 'optus_nbn_call_center'),('in_stage2_provider','=','optus')]
#             export_fields = [
#                 "optus_date", "optus_activation", "optus_order", "optus_customer",
#                 "optus_address", "optus_service", "optus_plan", "optus_per_month",
#                 "optus_center", "optus_salesperson", "optus_contact", "optus_email",
#                 "optus_notes", "optus_dcn", "optus_audit_1", "optus_audit_2"
#             ]
#         elif self.form_type == 'dodo_nbn':
#             domain = [('lead_for', '=', 'optus_nbn_call_center')]
#             export_fields = [
#                 "do_nbn_receipt", "do_nbn_service", "do_nbn_plans", "do_nbn_current",
#                 "do_nbn_current_no", "do_nbn_title", "do_first_name", "do_last_name",
#                 "do_mobile_no", "do_installation_address", "do_house_number",
#                 "do_street_name", "do_street_type", "do_suburb", "do_state",
#                 "do_post_code", "do_sale_date", "do_center_name", "do_closer_name",
#                 "do_dnc_ref_no", "do_dnc_exp_date", "do_audit_1", "do_audit_2"
#             ]

#         elif self.form_type == 'home_moving':
#             domain = [('lead_for','=','home_moving')]
#             export_fields = [
#                 "hm_moving_date", "hm_address", "hm_property_type", "hm_ownership",
#                 "hm_status", "hm_first_name", "hm_last_name", "hm_job_title", "hm_dob",
#                 "hm_friend_code", "hm_mobile", "hm_work_phone", "hm_home_phone",
#                 "hm_email", "hm_how_heard", "hm_agency_name", "hm_broker_name",
#                 "hm_agency_contact_number", "hm_connect_electricity", "hm_connect_gas",
#                 "hm_connect_internet", "hm_connect_water", "hm_connect_tv",
#                 "hm_connect_removalist", "hm_accept_terms"
#             ]

#         elif self.form_type == 'business_loan':
#             domain = [('lead_for','=','business_loan')] 
#             export_fields = [
#                 "bs_amount_to_borrow", "bs_business_name", "bs_trading_duration",
#                 "bs_monthly_turnover", "bs_first_name", "bs_last_name",
#                 "bs_email", "bs_home_owner", "bs_accept_terms"
#             ]  

#         elif self.form_type == 'home_loan':
#             domain = [('lead_for','=','home_loan')]
#             export_fields = [
#                 "hl_user_want_to", "hl_expected_price", "hl_deposit_amount",
#                 "hl_buying_reason", "hl_first_home_buyer", "hl_property_type",
#                 "hl_property_usage", "hl_credit_history", "hl_income_source",
#                 "hl_first_name", "hl_last_name", "hl_contact", "hl_email",
#                 "hl_accept_terms"
#             ]  

#         elif self.form_type == 'insurance':
#             domain = [('lead_for','=','insurance')]   
#             export_fields = [
#                 "hi_current_address", "hi_cover_type", "hi_have_insurance_cover",
#                 "hi_insurance_considerations", "hi_dob", "hi_annual_taxable_income",
#                 "hi_full_name", "hi_contact_number", "hi_email"
#             ]

#         elif self.form_type == 'veu':
#             domain = [('lead_for','=','veu')]
#             export_fields = [
#                 "u_first_name", "u_last_name", "u_mobile_no", "u_email",
#                 "u_post_code", "u_interested_in", "u_how", "u_accept_terms"
#             ] 

#         if self.start_date:
#             domain.append(('create_date', '>=', self.start_date))
#         if self.end_date:
#             domain.append(('create_date', '<=', self.end_date))       

#         leads = self.env['crm.lead'].search(domain)

#         if not leads:
#             raise UserError("No leads found for selected export")

#         # Create Excel file in memory
#         output = io.BytesIO()
#         workbook = xlsxwriter.Workbook(output, {'in_memory': True})
#         worksheet = workbook.add_worksheet('Leads')

#         # Formats
#         header_fmt = workbook.add_format({
#             'bold': True,
#             'bg_color': '#DCE6F1',
#             'border': 1,
#             'align': 'center',
#             'valign': 'vcenter'
#         })
#         text_fmt = workbook.add_format({
#             'text_wrap': True,
#             'border': 1,
#             'valign': 'top'
#         })
#         title_fmt = workbook.add_format({
#             'bold': True,
#             'font_size': 14,
#             'align': 'center'
#         })

#         # Set column widths
#         worksheet.set_column(0, len(export_fields) - 1, 20)

#         # Title
#         worksheet.merge_range(0, 0, 0, len(export_fields) - 1, 
#                             f"Lead Export - {self.form_type.replace('_', ' ').title()}", 
#                             title_fmt)

#         # Write headers
#         for col_idx, field in enumerate(export_fields):
#             field_obj = self.env['crm.lead']._fields.get(field)
#             display_name = field_obj.string if field_obj else field
#             worksheet.write(1, col_idx, display_name, header_fmt)

#         # Write data rows
#         for row_idx, lead in enumerate(leads, 2):
#             for col_idx, field in enumerate(export_fields):
#                 value = self._get_field_value(lead, field)
#                 worksheet.write(row_idx, col_idx, value, text_fmt)

#         # Footer
#         footer_text = f"Exported by {self.env.user.name} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
#         worksheet.merge_range(len(leads) + 3, 0, len(leads) + 3, len(export_fields) - 1,
#                             footer_text,
#                             workbook.add_format({'italic': True, 'align': 'right'}))

#         workbook.close()
#         output.seek(0)
#         file_data = output.read()

#         # Create attachment
#         file_name = f"{self.form_type}_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
#         attachment = self.env['ir.attachment'].create({
#             'name': file_name,
#             'type': 'binary',
#             'datas': base64.b64encode(file_data),
#             'res_model': self._name,
#             'res_id': self.id,
#             'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#         })

#         return {
#             'type': 'ir.actions.act_url',
#             'url': f"/web/content/{attachment.id}?download=true",
#             'target': 'self',
#         }

#     def _get_field_value(self, lead, field_name):
#         """Get and format field value based on field type"""
#         try:
#             field_obj = lead._fields.get(field_name)
#             if not field_obj:
#                 return ''

#             value = getattr(lead, field_name, None)

#             if not value:
#                 return ''

#             # Handle different field types
#             if field_obj.type == 'many2one':
#                 return value.display_name if value else ''
#             elif field_obj.type in ('many2many', 'one2many'):
#                 return ', '.join(rec.display_name for rec in value) if value else ''
#             elif field_obj.type == 'selection':
#                 if value:
#                     try:
#                         selection_dict = dict(field_obj.selection) if not callable(field_obj.selection) else {}
#                         return selection_dict.get(value, str(value))
#                     except:
#                         return str(value)
#                 return ''
#             elif field_obj.type == 'boolean':
#                 return "Yes" if value else "No"
#             elif field_obj.type in ('date', 'datetime'):
#                 if isinstance(value, datetime):
#                     return value.strftime("%Y-%m-%d %H:%M:%S")
#                 return str(value) if value else ''
#             elif field_obj.type == 'monetary':
#                 return f"{value:.2f}" if value else '0.00'
#             elif field_obj.type == 'float':
#                 return f"{value:.2f}" if value else '0.00'
#             else:
#                 return str(value) if value else ''

#         except Exception as e:
#             _logger.warning(f"Error reading field {field_name}: {str(e)}")
#             return ''