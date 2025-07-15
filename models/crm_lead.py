from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    external_api_id = fields.Integer("External API ID", index=True)
    vicidial_lead_id = fields.Integer("Vicidial Lead Id")
    selected_tab = fields.Char("Selected Tab", compute="_compute_selected_tab", store=False)


    services = fields.Selection([
        ("false" , "Select a service"),
        ('credit_card', 'Credit Card'),
        ('energy', 'Energy (compare plans from leading retailers)'),
        ('broadband', 'Broadband (fast broadband at lower cost)'),
        ('business_loan', 'Business Loan'),
        ('insurance', 'Health Insurance'),
        ('home_loan', 'Home Loan'),
        # ('energy_upgrades', 'Victorian Energy Upgrades'),
        ('moving_home', 'New Connection (Moving Home)'),
    ], string="Utility Services : ", default="false", required=True)

    @api.onchange('services')
    def _compute_selected_tab(self):
        for rec in self:
            rec.selected_tab = ''
            if rec.services == 'credit_card':
                rec.selected_tab = 'credit_card_tab'
            elif rec.services == 'false':
                rec.selected_tab = 'nothing_tab'    

            elif rec.services == 'energy':
                rec.selected_tab = 'energy_tab'
            elif rec.services == 'moving_home':
                rec.selected_tab = 'home_moving_tab'
            elif rec.services == 'broadband':
                rec.selected_tab == 'broadband_tab'
            elif rec.services == 'business_loan':
                rec.selected_tab =  'business_loan_tab'
            elif rec.services == 'insurance':
                rec.selected_tab = 'insurance_tab'
            elif rec.services == 'home_loan':
                rec.selected_tab = 'home_loab_tab'           



    show_credit_card_tab = fields.Boolean(
        compute="_compute_show_credit_card_tab"
    )

    show_nothing_tab = fields.Boolean(
        compute = "_compute_show_nothing_tab"
    )

    show_home_moving_tab = fields.Boolean(
        compute = "_compute_show_home_moving_tab"
    )

    show_energy_tab = fields.Boolean(
        compute = "_compute_show_energy_tab"
    )

    show_internet_tab = fields.Boolean(
        compute = "_compute_show_internet_tab"
    )

    show_business_loan_tab = fields.Boolean(
        compute = "_compute_show_business_loan_tab"
    )

    show_home_loan_tab = fields.Boolean(
        compute = "_compute_show_home_loan_tab"
    ) 

    show_health_insurance_tab = fields.Boolean(
        compute = "_compute_show_health_insurance_tab"
    )  

    @api.depends('services')
    def _compute_show_credit_card_tab(self):
        for rec in self:
            rec.show_credit_card_tab = rec.services == 'credit_card'



    @api.onchange('services')
    def _onchange_services_set_stage_dynamic(self):
            _logger.info("🟢 lead ID: %s | service: %s", self._origin.id, self.services)
            # if not self.services or self.services == "":
            #     _logger.info("🚫 Skipping stage setup for empty or invalid service.")
            #     return

            # if not self.services:
                # return
            
            
            # 🚫 Prevent running for credit_card if it's just default and lead not yet saved
            # if self.services == 'credit_card' and not self._origin.id:
            #     _logger.info("⚠️ Skipping credit_card stage auto-set (default selection on new lead)")
            #     return

            # Map each service to its corresponding model and stage field
            service_model_map = {
                'credit_card': ('custom.credit.card.form', 'cc_stage'),
                'moving_home': ('custom.home.moving.form', 'hm_home_stage'),
                'energy': ('custom.energy.compare.form', 'en_energy_stage'),
                'broadband': ('custom.broadband.form.data', 'in_internet_stage'),
                'business_loan': ('custom.business.loan.data', 'bs_business_loan_stage'),
                'insurance': ('custom.health.insurance.form.data', 'hi_stage'),
                'home_loan': ('custom.home.loan.data', 'hl_home_loan_stage')
            }

            # Get model name and stage field dynamically
            model_info = service_model_map.get(self.services)
            if not model_info:
                _logger.warning("⚠️ No model mapping for service: %s", self.services)
                return

            model_name, stage_field = model_info

            # 🔍 Search for submitted records
            submitted_stages = self.env[model_name].search([
                ('lead_id', '=', self._origin.id),
            ]).mapped('stage')

            _logger.info("📥 Submitted stages for %s: %s", model_name, submitted_stages)

            submitted_stages = [s for s in submitted_stages if s and s.isdigit()]

            # Determine next stage
            if not submitted_stages:
                next_stage = '1'
            else:
                max_stage = max(int(s) for s in submitted_stages)
                next_stage = str(min(max_stage + 1, 5))

            setattr(self, stage_field, next_stage)
            _logger.info("✅ Set %s = %s", stage_field, next_stage)

        






    @api.depends('services')
    def _compute_show_home_moving_tab(self):
        for rec in self:
            rec.show_home_moving_tab = rec.services == 'moving_home'


    @api.depends('services')
    def _compute_show_nothing_tab(self):
        for rec in self:
            rec.show_nothing_tab = rec.services == "false"        
            

    @api.depends('services')
    def _compute_show_energy_tab(self):
        for rec in self:
            rec.show_energy_tab = rec.services == 'energy' 

    @api.depends('services')
    def _compute_show_internet_tab(self):
        for rec in self:
            rec.show_internet_tab = rec.services == 'broadband'    

    @api.depends('services')
    def _compute_show_business_loan_tab(self):
        for rec in self:
            rec.show_business_loan_tab = rec.services == 'business_loan'

    @api.depends('services')
    def _compute_show_home_loan_tab(self):
        for rec in self:
            rec.show_home_loan_tab = rec.services == 'home_loan' 

    @api.depends('services')
    def _compute_show_health_insurance_tab(self):
        for rec in self:
            rec.show_health_insurance_tab = rec.services == 'insurance'   

    def create(self, vals):
        _logger.info("🔄 CREATE triggered with vals: %s", vals)
        lead = super().create(vals)
        lead._run_form_stage_saver()
        return lead

    def write(self, vals):
        _logger.info("🔄 WRITE triggered with vals: %s", vals)
        res = super().write(vals)
        self._run_form_stage_saver()
        return res 

    def _run_form_stage_saver(self):
        for lead in self:
            if lead.services == 'credit_card':
                lead._sync_credit_card_form_to_stage()
            elif lead.services == 'energy':
                lead._save_energy_stage_data()
            elif lead.services == 'moving_home':
                lead._save_home_moving_stage_data()
            elif lead.services == 'broadband':
                lead._sync_broadband_form_to_stage()
            elif lead.services == 'business_loan':
                lead._sync_business_loan_form_to_stage()
            elif lead.services == 'insurance':
                lead._sync_health_insurance_form_to_stage()
            elif lead.services == 'home_loan':
                lead._sync_home_loan_form_to_stage()
            elif lead.services == 'energy':
                lead._save_energy_stage_data()
            else:
                _logger.warning("⚠️ No handler defined for service: %s", lead.services)                                  

    # CREDIT CARD FORM              
    cc_stage = fields.Selection(
    [('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Credit Card Stage",
    default='1')
    cc_prefix = fields.Selection([
        ('n/a', 'N/A'), ('mr', 'Mr.'), ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('dr', 'Dr.'), ('miss', 'Miss')
    ], string="Prefix")
    cc_first_name = fields.Char("First Name")
    cc_last_name = fields.Char("Last Name")
    cc_job_title = fields.Char("Job Title")
    cc_phone = fields.Char("Phone")
    cc_email = fields.Char("Email")
    cc_annual_revenue = fields.Selection([
        ('under_2m', 'Under ~ $2M'), ('2m_10m', '$2M ~ $10M'), ('10m_50m', '$10M ~ $50M'), ('50m_100m', '$50M ~ $100M'), ('100m_above', 'Above $100M')
    ], string="Annual Revenue")
    cc_annual_spend = fields.Char("Annual Spend")
    cc_existing_products = fields.Char("Existing Competitor Products")
    cc_expense_tools = fields.Char("Expense Management Tools")
    cc_additional_info = fields.Text("Additional information for sales team")
    cc_consent_personal_info = fields.Boolean(
        string="I have obtained the express consent of the above individual to provide their personal information as noted above to American Express for purposes of offering American Express Commercial Payment Products to the business of the individual."
    )
    cc_consent_contact_method = fields.Selection([
        ('phone', 'Phone'),
        ('email', 'Email')
    ], string="I have obtained the consent of above companies to contact the appointed representative via")

    cc_contact_preference = fields.Selection([
        ('me_first', 'Me first'),
        ('referred_first', 'The referred contact first')
    ], string="In order to best process this lead the salesperson should contact")

    # @api.model
    # def create(self, vals):
    #     _logger.info("🟡 CUSTOM CREATE TRIGGERED with vals: %s", vals)
    #     lead = super().create(vals)
    #     lead._sync_credit_card_form_to_stage()
    #     return lead

    # def write(self, vals):
    #     _logger.info("🟡 CUSTOM WRITE TRIGGERED with vals: %s", vals)
    #     res = super().write(vals)
    #     self._sync_credit_card_form_to_stage()
    #     return res


    def _sync_credit_card_form_to_stage(self):

        for lead in self:
            _logger.info("🟢 Lead services: %s | stage: %s | ID: %s", lead.services, lead.cc_stage, lead.id)
            if lead.services != 'credit_card':
                continue

            stage = lead.cc_stage
            _logger.info("stage is %s ", stage)
            if not stage:
                _logger.warning("⚠️ No stage found for lead: %s", lead.id)
                continue

            CreditCardForm = self.env['custom.credit.card.form']

            # Check if record for this lead and stage exists
            existing = CreditCardForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', lead.cc_stage)
            ], limit=1)

            cc_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'prefix': lead.cc_prefix,
                'first_name': lead.cc_first_name,
                'last_name': lead.cc_last_name,
                'job_title': lead.cc_job_title,
                'phone': lead.cc_phone,
                'email': lead.cc_email,
                'annual_revenue': lead.cc_annual_revenue,
                'annual_spend': lead.cc_annual_spend,
                'existing_products': lead.cc_existing_products,
                'expense_tools': lead.cc_expense_tools,
                'additional_info': lead.cc_additional_info,
                'consent_personal_info': lead.cc_consent_personal_info,
                'consent_contact_method': lead.cc_consent_contact_method,
                'contact_preference': lead.cc_contact_preference,
            }

            if existing:
                existing.write(cc_vals)
            else:
                self.env['custom.credit.card.form'].create(cc_vals)


    @api.onchange('cc_stage')
    def _onchange_cc_stage(self):
        for rec in self:
            if rec.services != 'credit_card':
                return

            record = self.env['custom.credit.card.form'].search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.cc_stage)
            ], limit=1)
            
            _logger.info("Fetched credit card form for lead %s", rec._origin.id)

            if record:
                rec.cc_prefix = record.prefix
                rec.cc_first_name = record.first_name
                rec.cc_last_name = record.last_name
                rec.cc_job_title = record.job_title
                rec.cc_phone = record.phone
                rec.cc_email = record.email
                rec.cc_annual_revenue = record.annual_revenue
                rec.cc_annual_spend = record.annual_spend
                rec.cc_existing_products = record.existing_products
                rec.cc_expense_tools = record.expense_tools
                rec.cc_additional_info = record.additional_info
                rec.cc_consent_personal_info = record.consent_personal_info
                rec.cc_consent_contact_method = record.consent_contact_method
                rec.cc_contact_preference = record.contact_preference
            else:
                rec.cc_prefix = False
                rec.cc_first_name = False
                rec.cc_last_name = False
                rec.cc_job_title = False
                rec.cc_phone = False
                rec.cc_email = False
                rec.cc_annual_revenue = False
                rec.cc_annual_spend = False
                rec.cc_existing_products = False
                rec.cc_expense_tools = False
                rec.cc_additional_info = False
                rec.cc_consent_personal_info = False
                rec.cc_consent_contact_method = False
                rec.cc_contact_preference = False        


    # HOME MOVING FORM DATA
    hm_home_stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Home Moving Stage", default="1")
    hm_moving_date = fields.Date("Moving Date")
    hm_address = fields.Char("Address")
    hm_suburb = fields.Char("Suburb")
    hm_state = fields.Char("State")
    hm_postcode = fields.Char("Postcode")
    hm_first_name = fields.Char("First Name")
    hm_last_name = fields.Char("Last Name")
    hm_job_title = fields.Char("Job Title")
    hm_dob = fields.Date("Date of Birth")
    hm_friend_code = fields.Char("Refer a Friend Code")
    hm_mobile = fields.Char("Mobile")
    hm_work_phone = fields.Char("Work Phone")
    hm_email = fields.Char("Email")
    hm_how_heard = fields.Selection([
        ('google', 'Google'),
        ('social', 'Social Media'),
        ('friend', 'Friend Referral'),
        ('other', 'Other')
    ], string="How did you hear about us?")
    hm_connect_electricity = fields.Boolean("Electricity")
    hm_connect_gas = fields.Boolean("Gas")
    hm_connect_internet = fields.Boolean("Internet")
    hm_connect_water = fields.Boolean("Water")
    hm_connect_tv = fields.Boolean("Pay TV")
    hm_connect_removalist = fields.Boolean("Removalist")
    hm_accept_terms = fields.Boolean("I accept the Terms and Conditions")
    hm_recaptcha_checked = fields.Boolean("I'm not a robot")


    def _save_home_moving_stage_data(self):
        _logger.info("running home moving form data......")
        for rec in self:
            if rec.services != 'moving_home' or not rec.hm_home_stage:
                return

            existing = self.env['custom.home.moving.form'].search([
                ('lead_id', '=', rec.id),
                ('stage', '=', rec.hm_home_stage)
            ], limit=1)

            data = {
                'lead_id': rec.id,
                'stage': rec.hm_home_stage,
                'moving_date': rec.hm_moving_date,
                'address': rec.hm_address,
                'suburb': rec.hm_suburb,
                'state': rec.hm_state,
                'postcode': rec.hm_postcode,
                'first_name': rec.hm_first_name,
                'last_name': rec.hm_last_name,
                'job_title': rec.hm_job_title,
                'dob': rec.hm_dob,
                'friend_code': rec.hm_friend_code,
                'mobile': rec.hm_mobile,
                'work_phone': rec.hm_work_phone,
                'email': rec.hm_email,
                'how_heard': rec.hm_how_heard,
                'connect_electricity': rec.hm_connect_electricity,
                'connect_gas': rec.hm_connect_gas,
                'connect_internet': rec.hm_connect_internet,
                'connect_water': rec.hm_connect_water,
                'connect_tv': rec.hm_connect_tv,
                'connect_removalist': rec.hm_connect_removalist,
                'accept_terms': rec.hm_accept_terms,
                'recaptcha_checked': rec.hm_recaptcha_checked,
                'stage': rec.hm_home_stage,

            }

            if existing:
                existing.write(data)
            else:
                self.env['custom.home.moving.form'].create(data)

    @api.onchange('hm_home_stage')
    def _onchange_home_stage(self):
        for rec in self:
            if rec.services != 'moving_home':
                return
            
            record = self.env['custom.home.moving.form'].search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.hm_home_stage)
            ], limit=1)

            _logger.info("Loaded Home Moving Record: %s %s", rec._origin.id, rec.hm_home_stage)

            if record:
                rec.hm_moving_date = record.moving_date
                rec.hm_address = record.address
                rec.hm_suburb = record.suburb
                rec.hm_state = record.state
                rec.hm_postcode = record.postcode

                rec.hm_first_name = record.first_name
                rec.hm_last_name = record.last_name
                rec.hm_job_title = record.job_title
                rec.hm_dob = record.dob
                rec.hm_friend_code = record.friend_code

                rec.hm_mobile = record.mobile
                rec.hm_work_phone = record.work_phone
                rec.hm_email = record.email
                rec.hm_how_heard = record.how_heard

                rec.hm_connect_electricity = record.connect_electricity
                rec.hm_connect_gas = record.connect_gas
                rec.hm_connect_internet = record.connect_internet
                rec.hm_connect_water = record.connect_water
                rec.hm_connect_tv = record.connect_tv
                rec.hm_connect_removalist = record.connect_removalist

                rec.hm_accept_terms = record.accept_terms
                rec.hm_recaptcha_checked = record.recaptcha_checked
            else:
                # Clear if no record
                rec.hm_moving_date = False
                rec.hm_address = False
                rec.hm_suburb = False
                rec.hm_state = False
                rec.hm_postcode = False

                rec.hm_first_name = False
                rec.hm_last_name = False
                rec.hm_job_title = False
                rec.hm_dob = False
                rec.hm_friend_code = False

                rec.hm_mobile = False
                rec.hm_work_phone = False
                rec.hm_email = False
                rec.hm_how_heard = False

                rec.hm_connect_electricity = False
                rec.hm_connect_gas = False
                rec.hm_connect_internet = False
                rec.hm_connect_water = False
                rec.hm_connect_tv = False
                rec.hm_connect_removalist = False

                rec.hm_accept_terms = False
                rec.hm_recaptcha_checked = False
            

#     #ENERGY PLAN FORM
    en_energy_stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Energy Plans Stage", default="1")
    en_current_address = fields.Char(string="Current Address")
    en_what_to_compare = fields.Selection([
        ('electricity_gas', 'Electricity & Gas'),
        ('electricity', 'Elecricity'),
    ], string="What are you looking to compare?")
    en_property_type = fields.Selection([
        ('residential', 'Residential'),
        ('business', 'Business'),
    ], string="What type of property?")
    en_moving_in = fields.Boolean(string="Are you moving into this property?")
    en_date = fields.Date("date")
    en_property_ownership = fields.Selection([
        ('own', 'Own'),
        ('rent', 'Rent'),
    ], string="Do you own or rent this property?")
    en_usage_profile = fields.Selection([
        ('low', '1-2 people, spemd minimal time at home, weekly washing, minimal heating, cooking.'),
        ('medium', '3-4 people, home in the evening and weekend regular washing, heating and cooling.'),
        ('high', '5+ people, home during the day, evenings and weekend daily washing, heating and cooling.')
    ], string="Usage Profile")
    en_require_life_support = fields.Boolean(string="Does anyone residing or intending to reside at your premises require life support equipment?")
    en_concesion_card_holder = fields.Boolean("Are you a concession card holder?")
    en_rooftop_solar = fields.Boolean(string="Do you have rooftop solar panels")
    en_electricity_provider = fields.Selection([
        ('1st_energy', '1st Energy'),
        ('actew_agl', 'ActewAGL'),
        ('agl', 'AGL'),
        ('alinta_energy', 'Alinta Energy'),
        ('aus_power_gas', 'Australian Power & Gas'),
        ('blue_nrg', 'BlueNRG'),
        ('click_energy', 'Click Energy'),
        ('dodo_energy', 'Dodo Energy'),
        ('energy_australia', 'Energy Australia'),
        ('lumo_energy', 'Lumo Energy'),
        ('momentum_energy', 'Momentum Energy'),
        ('neighbourhood', 'Neighbourhood'),
        ('online_pow_gas', 'Online Power & Gas'),
        ('origin', 'Orgin'),
        ('people_energy', 'People Energy'),
        ('power_direct', 'Power Direct'),
        ('powershop', 'Powershop'),
        ('q_energy', 'QEnergy'),
        ('red_energy', 'Red Energy'),
        ('simple_energy', 'Simple Energy'),
        ('sumo_power', 'Sumo Power'),
        ('tango_energy', 'Tango Energy'),
        ('other', 'Other/Unknown'),

    ],"Current electricity provide")

    en_gas_provider = fields.Selection([
        ('1st_energy', '1st Energy'),
        ('actew_agl', 'ActewAGL'),
        ('agl', 'AGL'),
        ('alinta_energy', 'Alinta Energy'),
        ('aus_power_gas', 'Australian Power & Gas'),
        ('blue_nrg', 'BlueNRG'),
        ('click_energy', 'Click Energy'),
        ('dodo_energy', 'Dodo Energy'),
        ('energy_australia', 'Energy Australia'),
        ('lumo_energy', 'Lumo Energy'),
        ('momentum_energy', 'Momentum Energy'),
        ('neighbourhood', 'Neighbourhood'),
        ('online_pow_gas', 'Online Power & Gas'),
        ('origin', 'Orgin'),
        ('people_energy', 'People Energy'),
        ('power_direct', 'Power Direct'),
        ('powershop', 'Powershop'),
        ('q_energy', 'QEnergy'),
        ('red_energy', 'Red Energy'),
        ('simple_energy', 'Simple Energy'),
        ('sumo_power', 'Sumo Power'),
        ('tango_energy', 'Tango Energy'),
        ('other', 'Other/Unknown'),

    ],"Current gas provide")
    en_name = fields.Char("name")
    en_contact_number = fields.Char("contact_number")
    en_email = fields.Char("email")
    en_request_callback = fields.Boolean(string="Request a call back")
    en_accpeting_terms = fields.Boolean(string="By submitting your details you agree that you have read and agreed to the Terms and Conditions and Privacy Policy.")

    # @api.model
    # def create(self, vals):
    #     _logger.info("method to create plan is called")
    #     lead = super().create(vals)
    #     lead._save_energy_stage_data()
    #     return lead

    # def write(self, vals):
    #     res = super().write(vals)
    #     self._save_energy_stage_data()
    #     return res


    def _save_energy_stage_data(self):
        for rec in self:
            if not rec.en_energy_stage:
                continue

            existing = self.env['custom.energy.compare.form'].search([
                ('lead_id', '=', rec.id),
                ('stage', '=', rec.en_energy_stage)
            ], limit=1)

            data = {
                'lead_id': rec.id,
                'stage': rec.en_energy_stage,
                'current_address': rec.en_current_address,
                'what_to_compare': rec.en_what_to_compare,
                'property_type': rec.en_property_type,
                'moving_in': rec.en_moving_in,
                'date': rec.en_date,
                'property_ownership': rec.en_property_ownership,
                'usage_profile': rec.en_usage_profile,
                'require_life_support': rec.en_require_life_support,
                'concesion_card_holder': rec.en_concesion_card_holder,
                'rooftop_solar': rec.en_rooftop_solar,
                'electricity_provider': rec.en_electricity_provider,
                'gas_provider': rec.en_gas_provider,
                'name': rec.en_name,
                'contact_number': rec.en_contact_number,
                'email': rec.en_email,
                'request_callback': rec.en_request_callback,
                'accpeting_terms': rec.en_accpeting_terms,
                'stage': rec.en_energy_stage,

            }

            if existing:
                existing.write(data)
            else:
                self.env['custom.energy.compare.form'].create(data)

    @api.onchange('en_energy_stage')
    def _onchange_energy_stage(self):
        for rec in self:
            if rec.services != 'energy':
                return
            
            if not rec.en_energy_stage:
                return

            record = self.env['custom.energy.compare.form'].search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.en_energy_stage)
            ], limit=1)

        if record:
            rec.en_current_address = record.current_address
            rec.en_what_to_compare = record.what_to_compare
            rec.en_property_type = record.property_type
            rec.en_moving_in = record.moving_in
            rec.en_date = record.date
            rec.en_property_ownership = record.property_ownership
            rec.en_usage_profile = record.usage_profile
            rec.en_require_life_support = record.require_life_support
            rec.en_concesion_card_holder = record.concesion_card_holder
            rec.en_rooftop_solar = record.rooftop_solar
            rec.en_electricity_provider = record.electricity_provider
            rec.en_gas_provider = record.gas_provider
            rec.en_name = record.name
            rec.en_contact_number = record.contact_number
            rec.en_email = record.email
            rec.en_request_callback = record.request_callback
            rec.en_accpeting_terms = record.accpeting_terms
        else:
            rec.en_current_address = False
            rec.en_what_to_compare = False
            rec.en_property_type = False
            rec.en_moving_in = False
            rec.en_date = False
            rec.en_property_ownership = False
            rec.en_usage_profile = False
            rec.en_require_life_support = False
            rec.en_concesion_card_holder = False
            rec.en_rooftop_solar = False
            rec.en_electricity_provider = False
            rec.en_gas_provider = False
            rec.en_name = False
            rec.en_contact_number = False
            rec.en_email = False
            rec.en_request_callback = False
            rec.en_accpeting_terms = False

    # INTERNET FORM
    in_internet_stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Internet Plans Stage", default="1")
    in_current_address = fields.Char(string="Current Address")
    in_internet_usage_type = fields.Selection([
        ("browsing_email", "Browsing and Email"),
        ("work", "Work and Study"),
        ("social_media", "Social Media"),
        ("gaming", "Online Gaming"),
        ("streaming", "Streaming video/TV/Movies")       
    ], string="Internet Usage Type")

    in_internet_users_count = fields.Integer(string="Number of Users")
    in_important_feature = fields.Selection([
        ("speed", "Speed"),
        ("price", "Price"),
        ("reliability", "Reliability"),      
    ], string="Most Important Feature")
    in_speed_preference = fields.Selection([
        ("25Mb", "25 Mbps"),
        ("50Mb", "50 Mbps"),
        ("100Mb", "100 Mbps"),
        ("not_sure", "Not Sure"),   
    ], string="Speed Preference")
    in_broadband_reason = fields.Selection([
        ("moving", "I am Moving"),
        ("better_plan", "I want a better plan"),
        ("connection", "I need broadband connected"),
    ], string="Reason for Broadband")
    in_when_to_connect_type = fields.Selection([
        ("asap", "ASAP"),
        ("dont_mind", "I don't mind"),
        ("specific_date", "Choose a date"),
    ], string="When would you like broadband connected?")
    in_when_to_connect_date = fields.Date(string="Select connection date?")
    in_compare_plans = fields.Boolean(string="Would you also like to comapre your energy plans to see if you could save?")
    in_name = fields.Char(string="Full Name")
    in_contact_number = fields.Char(string="Contact Number")
    in_email = fields.Char(string="Email")
    in_request_callback = fields.Boolean(string="Request Callback :")
    in_accept_terms = fields.Boolean(string="By submitting your details you agree that you have read and agreed to the Terms and Conditions and Privacy Policy.")

    # @api.model
    # def create(self, vals):
    #     lead = super().create(vals)
    #     lead._sync_broadband_form_to_stage()
    #     return lead

    # def write(self, vals):
    #     result = super().write(vals)
    #     self._sync_broadband_form_to_stage()
    #     return result

    def _sync_broadband_form_to_stage(self):
        """
        Save broadband form data per stage in custom.broadband.form.data
        """
        for lead in self:
            stage = lead.in_internet_stage
            if not stage:
                continue

            BroadbandForm = self.env['custom.broadband.form.data']

            # Check if record for this lead and stage exists
            existing = BroadbandForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            broadband_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'current_address': lead.in_current_address,
                'internet_usage_type': lead.in_internet_usage_type,
                'internet_users_count': lead.in_internet_users_count,
                'important_feature': lead.in_important_feature,
                'speed_preference': lead.in_speed_preference,
                'broadband_reason': lead.in_broadband_reason,
                'when_to_connect_type': lead.in_when_to_connect_type,
                'when_to_connect_date': lead.in_when_to_connect_date,
                'compare_plans': lead.in_compare_plans,
                'name': lead.in_name,
                'contact_number': lead.in_contact_number,
                'email': lead.in_email,
                'request_callback': lead.in_request_callback,
                'accept_terms': lead.in_accept_terms,
                'stage': lead.in_internet_stage,

            }

            if existing:
                existing.write(broadband_vals)
            else:
                BroadbandForm.create(broadband_vals)

    @api.onchange('in_internet_stage')
    def _onchange_in_internet_stage(self):
        """
        Load saved broadband form data for selected stage into the current lead
        """
        if not self.in_internet_stage:
            return

        broadband_data = self.env['custom.broadband.form.data'].search([
            ('lead_id', '=', self._origin.id),
            ('stage', '=', self.in_internet_stage)
        ], limit=1)

        if broadband_data:
            self.in_current_address = broadband_data.current_address
            self.in_internet_usage_type = broadband_data.internet_usage_type
            self.in_internet_users_count = broadband_data.internet_users_count
            self.in_important_feature = broadband_data.important_feature
            self.in_speed_preference = broadband_data.speed_preference
            self.in_broadband_reason = broadband_data.broadband_reason
            self.in_when_to_connect_type = broadband_data.when_to_connect_type
            self.in_when_to_connect_date = broadband_data.when_to_connect_date
            self.in_compare_plans = broadband_data.compare_plans
            self.in_name = broadband_data.name
            self.in_contact_number = broadband_data.contact_number
            self.in_email = broadband_data.email
            self.in_request_callback = broadband_data.request_callback
            self.in_accept_terms = broadband_data.accept_terms
        else:
            # Optional: clear fields if no data is saved for the new stage
            self.in_current_address = False
            self.in_internet_usage_type = False
            self.in_internet_users_count = False
            self.in_important_feature = False
            self.in_speed_preference = False
            self.in_broadband_reason = False
            self.in_when_to_connect_type = False
            self.in_when_to_connect_date = False
            self.in_compare_plans = False
            self.in_name = False
            self.in_contact_number = False
            self.in_email = False
            self.in_request_callback = False
            self.in_accept_terms = False                

    # UNSECURED BUSINESS LOAN
    bs_business_loan_stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Business Loan Plans Stage", default="1")
    bs_amount_to_borrow = fields.Integer(string="How much would you like to borrow?")
    bs_business_name = fields.Char(string="Name of your business")
    bs_trading_duration = fields.Selection([
        ("0-6 months", "0-6 Months"),
        ("6-12 months", "6-12 Months"),
        ("12-24 months", "12-24 Months"),
        ("over 24 months", "Over 24 Months"),
    ],string="How long have you been trading")
    bs_monthly_turnover = fields.Integer(string="What is your monthly turnover")
    bs_first_name = fields.Char(string="First Name")
    bs_last_name = fields.Char(string="Last Name")
    bs_email = fields.Char(string="Email")
    bs_home_owner = fields.Boolean(string="Are you a home owner?")
    bs_accept_terms = fields.Boolean(string="Accept terms and conditions")

    # @api.model
    # def create(self, vals):
    #     lead = super().create(vals)
    #     lead._sync_business_loan_form_to_stage()
    #     return lead

    # def write(self, vals):
    #     result = super().write(vals)
    #     self._sync_business_loan_form_to_stage()
    #     return result

    def _sync_business_loan_form_to_stage(self):
        """
        Save business loan form data per stage in custom.business.loan.form.data
        """
        for lead in self:
            stage = lead.bs_business_loan_stage
            if not stage:
                continue

            BusinessLoanForm = self.env['custom.business.loan.data']

            existing = BusinessLoanForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            business_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'amount_to_borrow': lead.bs_amount_to_borrow,
                'business_name': lead.bs_business_name,
                'trading_duration': lead.bs_trading_duration,
                'monthly_turnover': lead.bs_monthly_turnover,
                'first_name': lead.bs_first_name,
                'last_name': lead.bs_last_name,
                'email': lead.bs_email,
                'home_owner': lead.bs_home_owner,
                'accept_terms': lead.bs_accept_terms,
                'stage': lead.bs_business_loan_stage,

            }

            if existing:
                existing.write(business_vals)
            else:
                BusinessLoanForm.create(business_vals)

    @api.onchange('bs_business_loan_stage')
    def _onchange_bs_business_loan_stage(self):
        """
        Auto-load previously saved business loan form data when stage changes
        """
        if not self.bs_business_loan_stage:
            return

        BusinessLoanForm = self.env['custom.business.loan.data']

        existing = BusinessLoanForm.search([
            ('lead_id', '=', self._origin.id),
            ('stage', '=', self.bs_business_loan_stage)
        ], limit=1)

        if existing:
            self.bs_amount_to_borrow = existing.amount_to_borrow
            self.bs_business_name = existing.business_name
            self.bs_trading_duration = existing.trading_duration
            self.bs_monthly_turnover = existing.monthly_turnover
            self.bs_first_name = existing.first_name
            self.bs_last_name = existing.last_name
            self.bs_email = existing.email
            self.bs_home_owner = existing.home_owner
            self.bs_accept_terms = existing.accept_terms
        else:
            # Clear the fields if no record exists for this stage
            self.bs_amount_to_borrow = False
            self.bs_business_name = False
            self.bs_trading_duration = False
            self.bs_monthly_turnover = False
            self.bs_first_name = False
            self.bs_last_name = False
            self.bs_email = False
            self.bs_home_owner = False
            self.bs_accept_terms = False   

#    HOME LOAN FORM DATA
    hl_home_loan_stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Home Loan Plans Stage", default="1")
    hl_user_want_to = fields.Selection([
        ("refinance", "I want to refinance"),
        ("buy home", "I want to buy a home"),
    ],string="What would you like to do?")
    hl_expected_price = fields.Integer(string="What is your exptected price?")
    hl_deposit_amount = fields.Integer(string="How much deposit do you have?")
    hl_buying_reason = fields.Selection([
        ("just_exploring", "Just exploring options"),
        ("planning_to_buy", "Planning to buy home in next 6 months"),
        ("actively_looking", "Actively looking/made an offer"),
        ("exchanged_contracts", "Exchanged Contracts"),
    ],string="What best describes your home buying situation?")
    hl_first_home_buyer = fields.Boolean(string="Are you a first home buyer")
    hl_property_type = fields.Selection([
        ("established_home", "Established Home"),
        ("newly_built", "Newly built/off the plan"),
        ("vacant_land", "Vacant land to build on"),
    ],string="What kind of property are you looking for?")   
    hl_property_usage = fields.Selection([
        ("to_live", "I will live there"),
        ("for_investment", "It is for investment purposes"),
    ],string="How will this property be used?")
    hl_credit_history = fields.Selection([
        ("excellent", "Excellent - no issues"),
        ("average", "Average paid default"),
        ("fair", "Fair"),
        ("don't know", "I don't know"),
    ],string="What do you think your credit history is?")
    hl_income_source = fields.Selection([
        ("employee", "I am an employee"),
        ("business", "I have my own business"),
        ("other", "Other"),
    ],string="How do you earn your income?")
    hl_first_name = fields.Char(string="First Name")
    hl_last_name = fields.Char(string="Last Name")
    hl_contact = fields.Char(string="Contact Number")
    hl_email = fields.Char(string="Email")                  
    hl_accept_terms = fields.Boolean(string="Agree to accept terms and conditions")

    # @api.model
    # def create(self, vals):
    #     lead = super().create(vals)
    #     lead._sync_home_loan_form_to_stage()
    #     return lead

    # def write(self, vals):
    #     result = super().write(vals)
    #     self._sync_home_loan_form_to_stage()
    #     return result

    def _sync_home_loan_form_to_stage(self):
        """
        Save Home Loan form data per stage in custom.home.loan.form.data
        """
        for lead in self:
            stage = lead.hl_home_loan_stage
            if not stage:
                continue

            HomeLoanForm = self.env['custom.home.loan.data']

            existing = HomeLoanForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            home_loan_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'user_want_to': lead.hl_user_want_to,
                'expected_price': lead.hl_expected_price,
                'deposit_amount': lead.hl_deposit_amount,
                'buying_reason': lead.hl_buying_reason,
                'first_home_buyer': lead.hl_first_home_buyer,
                'property_type': lead.hl_property_type,
                'property_usage': lead.hl_property_usage,
                'credit_history': lead.hl_credit_history,
                'income_source': lead.hl_income_source,
                'first_name': lead.hl_first_name,
                'last_name': lead.hl_last_name,
                'contact': lead.hl_contact,
                'email': lead.hl_email,
                'accept_terms': lead.hl_accept_terms,
                'stage': lead.hl_home_loan_stage,

            }

            if existing:
                existing.write(home_loan_vals)
            else:
                HomeLoanForm.create(home_loan_vals)

   
    @api.onchange('hl_home_loan_stage')
    def _onchange_hl_home_loan_stage(self):
        """
        Load Home Loan form data from saved stage when the user changes stage.
        """
        if not self.hl_home_loan_stage:
            return

        HomeLoanForm = self.env['custom.home.loan.data']
        existing = HomeLoanForm.search([
            ('lead_id', '=', self._origin.id),
            ('stage', '=', self.hl_home_loan_stage)
        ], limit=1)
        _logger.info("home loan id is %s ", self._origin.id)
        if existing:
            self.hl_user_want_to = existing.user_want_to
            self.hl_expected_price = existing.expected_price
            self.hl_deposit_amount = existing.deposit_amount
            self.hl_buying_reason = existing.buying_reason
            self.hl_first_home_buyer = existing.first_home_buyer
            self.hl_property_type = existing.property_type
            self.hl_property_usage = existing.property_usage
            self.hl_credit_history = existing.credit_history
            self.hl_income_source = existing.income_source
            self.hl_first_name = existing.first_name
            self.hl_last_name = existing.last_name
            self.hl_contact = existing.contact
            self.hl_email = existing.email
            self.hl_accept_terms = existing.accept_terms
        else:
            # Reset fields if no existing data is found
            self.hl_user_want_to = False
            self.hl_expected_price = False
            self.hl_deposit_amount = False
            self.hl_buying_reason = False
            self.hl_first_home_buyer = False
            self.hl_property_type = False
            self.hl_property_usage = False
            self.hl_credit_history = False
            self.hl_income_source = False
            self.hl_first_name = False
            self.hl_last_name = False
            self.hl_contact = False
            self.hl_email = False
            self.hl_accept_terms = False    

    # HEALTH INSURANCE DATA   
    hi_stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')],
    string="Health Insurance Plans Stage", default="1")               
    hi_current_address = fields.Char(string="Current address")
    hi_cover_type = fields.Selection([
        ("hospital_extras", "Hospital + Extras"),
        ("hospital", "Hospital only"),
        ("extras", "Extras only"),
    ],string="Select type of cover")
    hi_have_insurance_cover = fields.Selection([
        ("yes","Yes"),
        ("no","No")
    ],string="Do you have health inssurance cover")
    hi_insurance_considerations = fields.Selection([
        ("health_concern","I have a specific health concern"),
        ("save_money","I am looking to save money on my health premium"),
        ("no_insurance_before","I haven't held health insurance before"),
        ("better_health_cover","I am looking for better health cover"),
        ("need_for_tax","I need it for my tax"),
        ("planning_a_baby","I am planning a baby"),
        ("changed_circumstances","My circumstances have changed"),
        ("compare_options","I just want to compare options"),
    ],string="What are your main considerations when looking for a new health insurance cover?")
    hi_dob = fields.Date(string="What is your date of birth")
    hi_annual_taxable_income = fields.Selection([
        ("$97,000_or_less","$97,000 or less (Base Tier)"),
        ("$97,001_$113,000","$97,001 - $113,000 (Tier 1)"),
        ("$113,001_$151,000","$113,001 - $151,000 (Tier 2)"),
        ("$151,001_or_more","$151,001 or more (Tier 3)")
    ],string="What is your annual taxable income?")
    hi_full_name = fields.Char(string="Full Name")
    hi_contact_number = fields.Char(string="Contact Number")
    hi_email = fields.Char(string="Email")

    # @api.model
    # def create(self, vals):
    #     lead = super().create(vals)
    #     lead._sync_health_insurance_form_to_stage()
    #     return lead

    # def write(self, vals):
    #     result = super().write(vals)
    #     self._sync_health_insurance_form_to_stage()
    #     return result

    def _sync_health_insurance_form_to_stage(self):
        """
        Save health insurance form data per stage in custom.health.insurance.form.data
        """
        for lead in self:
            stage = lead.hi_stage
            if not stage:
                continue

            HealthInsuranceForm = self.env['custom.health.insurance.form.data']

            # Check if record for this lead and stage exists
            existing = HealthInsuranceForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            hi_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'current_address': lead.hi_current_address,
                'cover_type': lead.hi_cover_type,
                'have_insurance_cover': lead.hi_have_insurance_cover,
                'insurance_considerations': lead.hi_insurance_considerations,
                'dob': lead.hi_dob,
                'annual_taxable_income': lead.hi_annual_taxable_income,
                'full_name': lead.hi_full_name,
                'contact_number': lead.hi_contact_number,
                'email': lead.hi_email,
            }

            if existing:
                existing.write(hi_vals)
            else:
                HealthInsuranceForm.create(hi_vals)

    @api.onchange('hi_stage')
    def _onchange_hi_stage(self):
        """
        Load Health Insurance form data from saved stage when the user changes stage.
        """
        if not self.hi_stage:
            return

        HealthInsuranceForm = self.env['custom.health.insurance.form.data']
        existing = HealthInsuranceForm.search([
            ('lead_id', '=', self._origin.id),
            ('stage', '=', self.hi_stage)
        ], limit=1)

        if existing:
            self.hi_current_address = existing.current_address
            self.hi_cover_type = existing.cover_type
            self.hi_have_insurance_cover = existing.have_insurance_cover
            self.hi_insurance_considerations = existing.insurance_considerations
            self.hi_dob = existing.dob
            self.hi_annual_taxable_income = existing.annual_taxable_income
            self.hi_full_name = existing.full_name
            self.hi_contact_number = existing.contact_number
            self.hi_email = existing.email
        else:
            # Reset fields if no existing data is found
            self.hi_current_address = False
            self.hi_cover_type = False
            self.hi_have_insurance_cover = False
            self.hi_insurance_considerations = False
            self.hi_dob = False
            self.hi_annual_taxable_income = False
            self.hi_full_name = False
            self.hi_contact_number = False
            self.hi_email = False            

           


   
