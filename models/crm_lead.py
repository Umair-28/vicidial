from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    external_api_id = fields.Integer("External API ID", index=True)
    vicidial_lead_id = fields.Integer("Vicidial Lead Id")
    selected_tab = fields.Char("Selected Tab", compute="_compute_selected_tab", store=False)
    partner_latitude = fields.Float(
        string='Latitude',
        related='partner_id.partner_latitude',
        store=True
    )

    partner_longitude = fields.Float(
        string='Longitude',
        related='partner_id.partner_longitude',
        store=True
    )

    # Example: Custom field for automatic assignment logic
    assignation_id = fields.Many2one(
        'res.partner',
        string='Automatically Assigned Partner'
    )

    # stage_id = fields.Many2one('crm.stage', string="Stage")

    


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
        ('dodo_nbn', 'DODO NBN Form'),
        ('optus_nbn', 'Optus NBN Form'),
        ('first_energy', 'First Energy Form'),
        ('dodo_power', 'DODO Power And Gas Form')
    ], string="Select Service", default="false", required=True)

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
            elif rec.services == 'dodo_nbn':
                rec.selected_tab = 'dodo_nbn_tab' 
            elif rec.services == 'optus_nbn':
                rec.selected_tab = 'optus_nbn_tab' 
            elif rec.services == 'first_energy':
                rec.selected_tab = 'first_energy_tab'  
            elif rec.services == 'dodo_power':
                rec.selected_tab = 'dodo_power_tab'                          



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

    show_dodo_nbn_tab = fields.Boolean(
        compute = "_compute_show_dodo_nbn_tab"
    )

    show_optus_nbn_tab = fields.Boolean(
        compute = "_compute_show_optus_nbn_tab"
    )

    show_first_energy_tab = fields.Boolean(
        compute = "_compute_show_first_energy_tab"
    )  

    show_dodo_power_tab = fields.Boolean(
        compute = "_compute_show_dodo_power_tab"
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
                'home_loan': ('custom.home.loan.data', 'hl_home_loan_stage'),
                'dodo_nbn':('custom.dodo.nbn.form', 'dodo_form_stage'),
                'optus_nbn':('custom.optus.nbn.form', 'optus_form_stage'),
                'first_energy':('custom.first.energy.form', 'first_energy_form_stage'),
                'dodo_power':('custom.dodo.power.form', 'dodo_power_stage')
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

    @api.depends('services')
    def _compute_show_dodo_nbn_tab(self):
        for rec in self:
            rec.show_dodo_nbn_tab = rec.services == 'dodo_nbn'

    @api.depends('services')
    def _compute_show_optus_nbn_tab(self):
        for rec in self:
            rec.show_optus_nbn_tab = rec.services ==  'optus_nbn'  

    @api.depends('services')
    def _compute_show_first_energy_tab(self):
        for rec in self:
            rec.show_first_energy_tab = rec.services ==  'first_energy' 

    @api.depends('services')
    def _compute_show_dodo_power_tab(self):
        for rec in self:
            rec.show_dodo_power_tab = rec.services ==  'dodo_power'   

    def create(self, vals):
        _logger.info("🔄 CREATE triggered with vals: %s", vals)

        # Create lead
        lead = super().create(vals)

        # Assign vicidial_lead_id after record exists
        if not vals.get("vicidial_lead_id"):
            lead.vicidial_lead_id = lead.id   # or link to vicidial record if needed
            _logger.info("✅ Vicidial Lead ID set to %s", lead.vicidial_lead_id)

        lead._run_form_stage_saver()
        return lead

    def write(self, vals):
        _logger.info("🔄 WRITE triggered with vals: %s", vals)

        res = super().write(vals)

        # Ensure vicidial_lead_id stays updated
        for record in self:
            if not vals.get("vicidial_lead_id") and not record.vicidial_lead_id:
                record.vicidial_lead_id = record.id
                _logger.info("✏️ Updated Vicidial Lead ID for %s", record.id)

            record._run_form_stage_saver()

        return res
                                       

    # def create(self, vals):
    #     _logger.info("🔄 CREATE triggered with vals: %s", vals)
    #     lead = super().create(vals)
    #     lead._run_form_stage_saver()
    #     return lead

    # def write(self, vals):
    #     _logger.info("🔄 WRITE triggered with vals: %s", vals)
    #     res = super().write(vals)
    #     self._run_form_stage_saver()
    #     return res 

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
            elif lead.services == 'dodo_nbn':
                lead._save_dodo_nbn_data()
            elif lead.services == 'optus_nbn':
                lead._save_optus_nbn_data() 
            elif lead.services == 'first_energy':
                lead._save_first_energy_data() 
            elif lead.services == 'dodo_power':
                lead._save_dodo_power_data()                   
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
                rec.cc_first_name = rec.contact_name or  False
                rec.cc_last_name = False
                rec.cc_job_title = False
                rec.cc_phone = rec.phone_sanitized or False
                rec.cc_email = rec.email_normalized or  False
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
                rec.hm_work_phone = rec.phone_sanitized or  False
                rec.hm_email = rec.email_normalized or False
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
            rec.en_name = rec.contact_name or False
            rec.en_contact_number = rec.phone_sanitized or  False
            rec.en_email = rec.email_normalized or  False
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
        for rec in self:
            if not rec.in_internet_stage:
                return

            broadband_data = self.env['custom.broadband.form.data'].search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.in_internet_stage)
            ], limit=1)

            if broadband_data:
                rec.in_current_address = broadband_data.current_address
                rec.in_internet_usage_type = broadband_data.internet_usage_type
                rec.in_internet_users_count = broadband_data.internet_users_count
                rec.in_important_feature = broadband_data.important_feature
                rec.in_speed_preference = broadband_data.speed_preference
                rec.in_broadband_reason = broadband_data.broadband_reason
                rec.in_when_to_connect_type = broadband_data.when_to_connect_type
                rec.in_when_to_connect_date = broadband_data.when_to_connect_date
                rec.in_compare_plans = broadband_data.compare_plans
                rec.in_name = broadband_data.name
                rec.in_contact_number = broadband_data.contact_number
                rec.in_email = broadband_data.email
                rec.in_request_callback = broadband_data.request_callback
                rec.in_accept_terms = broadband_data.accept_terms
            else:
                # Optional: clear fields if no data is saved for the new stage
                rec.in_current_address = False
                rec.in_internet_usage_type = False
                rec.in_internet_users_count = False
                rec.in_important_feature = False
                rec.in_speed_preference = False
                rec.in_broadband_reason = False
                rec.in_when_to_connect_type = False
                rec.in_when_to_connect_date = False
                rec.in_compare_plans = False
                rec.in_name = rec.contact_name or False  # Added default value
                rec.in_contact_number = rec.phone_sanitized or False
                rec.in_email = rec.email_normalized or False
                rec.in_request_callback = False
                rec.in_accept_terms = False              

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
        for rec in self:
            if not rec.bs_business_loan_stage:
                return

            BusinessLoanForm = self.env['custom.business.loan.data']

            existing = BusinessLoanForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.bs_business_loan_stage)
            ], limit=1)

            if existing:
                rec.bs_amount_to_borrow = existing.amount_to_borrow
                rec.bs_business_name = existing.business_name
                rec.bs_trading_duration = existing.trading_duration
                rec.bs_monthly_turnover = existing.monthly_turnover
                rec.bs_first_name = existing.first_name
                rec.bs_last_name = existing.last_name
                rec.bs_email = existing.email
                rec.bs_home_owner = existing.home_owner
                rec.bs_accept_terms = existing.accept_terms
            else:
                # Clear the fields if no record exists for this stage
                rec.bs_amount_to_borrow = False
                rec.bs_business_name = False
                rec.bs_trading_duration = False
                rec.bs_monthly_turnover = False
                rec.bs_first_name = rec.contact_name or False  # Added default value
                rec.bs_last_name = False
                rec.bs_email = rec.email_normalized or False  # Added default value
                rec.bs_home_owner = False
                rec.bs_accept_terms = False  

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
        for rec in self:
            if not rec.hl_home_loan_stage:
                return

            HomeLoanForm = self.env['custom.home.loan.data']
            existing = HomeLoanForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.hl_home_loan_stage)
            ], limit=1)
            _logger.info("home loan id is %s ", rec._origin.id)
            
            if existing:
                rec.hl_user_want_to = existing.user_want_to
                rec.hl_expected_price = existing.expected_price
                rec.hl_deposit_amount = existing.deposit_amount
                rec.hl_buying_reason = existing.buying_reason
                rec.hl_first_home_buyer = existing.first_home_buyer
                rec.hl_property_type = existing.property_type
                rec.hl_property_usage = existing.property_usage
                rec.hl_credit_history = existing.credit_history
                rec.hl_income_source = existing.income_source
                rec.hl_first_name = existing.first_name
                rec.hl_last_name = existing.last_name
                rec.hl_contact = existing.contact
                rec.hl_email = existing.email
                rec.hl_accept_terms = existing.accept_terms
            else:
                # Reset fields if no existing data is found
                rec.hl_user_want_to = False
                rec.hl_expected_price = False
                rec.hl_deposit_amount = False
                rec.hl_buying_reason = False
                rec.hl_first_home_buyer = False
                rec.hl_property_type = False
                rec.hl_property_usage = False
                rec.hl_credit_history = False
                rec.hl_income_source = False
                rec.hl_first_name = rec.contact_name or False  # Added default value
                rec.hl_last_name = False
                rec.hl_contact = rec.phone_sanitized or False  # Added default value
                rec.hl_email = rec.email_normalized or False  # Added default value
                rec.hl_accept_terms = False   

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
        for rec in self:
            if not rec.hi_stage:
                return

            HealthInsuranceForm = self.env['custom.health.insurance.form.data']
            existing = HealthInsuranceForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.hi_stage)
            ], limit=1)

            if existing:
                rec.hi_current_address = existing.current_address
                rec.hi_cover_type = existing.cover_type
                rec.hi_have_insurance_cover = existing.have_insurance_cover
                rec.hi_insurance_considerations = existing.insurance_considerations
                rec.hi_dob = existing.dob
                rec.hi_annual_taxable_income = existing.annual_taxable_income
                rec.hi_full_name = existing.full_name
                rec.hi_contact_number = existing.contact_number
                rec.hi_email = existing.email
            else:
                # Reset fields if no existing data is found
                rec.hi_current_address = False
                rec.hi_cover_type = False
                rec.hi_have_insurance_cover = False
                rec.hi_insurance_considerations = False
                rec.hi_dob = False
                rec.hi_annual_taxable_income = False
                rec.hi_full_name = rec.contact_name or False  # Added default value
                rec.hi_contact_number = rec.phone_sanitized or False  # Added default value
                rec.hi_email = rec.email_normalized or False  # Added default value

#  DODO FORM DATA

    dodo_form_stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='DODO Stage', default="1")
    do_dodo_receipt_no = fields.Char(string="DODO Receipt Number")
    do_service_type = fields.Char(string="Service Type")
    do_plan_sold_with_dodo = fields.Char(string="Plan With DODO")
    do_current_provider = fields.Char(string="Current Provider")
    do_current_provider_acc_no = fields.Char(string="Current Provider Account No")
    do_title = fields.Selection([
        ("mr", "MR"),
        ("mrs", "MRS"),
    ],string="Title")   
    do_first_name = fields.Char(string="First Name")
    do_last_name = fields.Char(string="Last Name")
    do_mobile_no = fields.Char(string="Mobile No")
    do_installation_address = fields.Char(string="Installation Address - Unit/Flat Number")
    do_house_number = fields.Char(string="House No")
    do_street_name = fields.Char(string="Street Name")
    do_street_type = fields.Char(string="Street Type")
    do_suburb = fields.Char(string="Installation address-Suburb")
    do_state = fields.Char(string="State")
    do_post_code = fields.Char("Post Code")
    do_sale_date = fields.Date(string="Sale Date")
    do_center_name = fields.Char(string="Center Name")
    do_closer_name = fields.Char(string="Closer Name")
    do_dnc_ref_no = fields.Char(string="DNC Reference No")
    do_dnc_exp_date = fields.Date(string="DNC Expiry Date")
    do_audit_1 = fields.Char(string="Audit 1")
    do_audit_2 = fields.Char(string="Audit 2")   

    def _save_dodo_nbn_data(self):
        """
        Save DODO NBN form data per stage in custom.dodo.nbn.form
        """
        for lead in self:
            stage = lead.dodo_form_stage
            if not stage:
                continue

            DodoForm = self.env['custom.dodo.nbn.form']

            # Check if record for this lead and stage exists
            existing = DodoForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            dodo_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'dodo_receipt_no': lead.do_dodo_receipt_no,
                'service_type': lead.do_service_type,
                'plan_sold_with_dodo': lead.do_plan_sold_with_dodo,
                'current_provider': lead.do_current_provider,
                'current_provider_acc_no': lead.do_current_provider_acc_no,
                'title': lead.do_title,
                'first_name': lead.do_first_name,
                'last_name': lead.do_last_name,
                'mobile_no': lead.do_mobile_no,
                'installation_address': lead.do_installation_address,
                'house_number': lead.do_house_number,
                'street_name': lead.do_street_name,
                'street_type': lead.do_street_type,
                'suburb': lead.do_suburb,
                'state': lead.do_state,
                'post_code': lead.do_post_code,
                'sale_date': lead.do_sale_date,
                'center_name': lead.do_center_name,
                'closer_name': lead.do_closer_name,
                'dnc_ref_no': lead.do_dnc_ref_no,
                'dnc_exp_date': lead.do_dnc_exp_date,
                'audit_1': lead.do_audit_1,
                'audit_2': lead.do_audit_2,
            }

            if existing:
                existing.write(dodo_vals)
            else:
                DodoForm.create(dodo_vals)

    # ------------------------
    # LOAD METHOD (ONCHANGE)
    # ------------------------
    @api.onchange('dodo_form_stage')
    def _onchange_dodo_form_stage(self):
        """
        Load DODO NBN form data from saved stage when the user changes stage.
        """
        for rec in self:
            if not rec.dodo_form_stage:
                return

            DodoForm = self.env['custom.dodo.nbn.form']
            existing = DodoForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.dodo_form_stage)
            ], limit=1)

            if existing:
                rec.do_dodo_receipt_no = existing.dodo_receipt_no
                rec.do_service_type = existing.service_type
                rec.do_plan_sold_with_dodo = existing.plan_sold_with_dodo
                rec.do_current_provider = existing.current_provider
                rec.do_current_provider_acc_no = existing.current_provider_acc_no
                rec.do_title = existing.title
                rec.do_first_name = existing.first_name
                rec.do_last_name = existing.last_name
                rec.do_mobile_no = existing.mobile_no
                rec.do_installation_address = existing.installation_address
                rec.do_house_number = existing.house_number
                rec.do_street_name = existing.street_name
                rec.do_street_type = existing.street_type
                rec.do_suburb = existing.suburb
                rec.do_state = existing.state
                rec.do_post_code = existing.post_code
                rec.do_sale_date = existing.sale_date
                rec.do_center_name = existing.center_name
                rec.do_closer_name = existing.closer_name
                rec.do_dnc_ref_no = existing.dnc_ref_no
                rec.do_dnc_exp_date = existing.dnc_exp_date
                rec.do_audit_1 = existing.audit_1
                rec.do_audit_2 = existing.audit_2
            else:
                # Reset fields if no existing data is found
                rec.do_dodo_receipt_no = False
                rec.do_service_type = False
                rec.do_plan_sold_with_dodo = False
                rec.do_current_provider = False
                rec.do_current_provider_acc_no = False
                rec.do_title = False
                rec.do_first_name = rec.contact_name or False  # default
                rec.do_last_name = False
                rec.do_mobile_no = rec.phone_sanitized or False  # default
                rec.do_installation_address = False
                rec.do_house_number = False
                rec.do_street_name = False
                rec.do_street_type = False
                rec.do_suburb = False
                rec.do_state = False
                rec.do_post_code = False
                rec.do_sale_date = False
                rec.do_center_name = False
                rec.do_closer_name = False
                rec.do_dnc_ref_no = False
                rec.do_dnc_exp_date = False
                rec.do_audit_1 = False
                rec.do_audit_2 = False 

    # OPTUS NBN FORM
    
    optus_form_stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='OPTUS Stage', default="1")
    op_sale_date = fields.Date(string="Sale Date")
    op_activation_date = fields.Date(string="Activation Date")
    op_order_no = fields.Char(string="Order Number")
    op_customer_name = fields.Char(string="Customer Name")
    op_service_address = fields.Char(string="Service Address")
    op_service = fields.Char(string="Service")
    op_plan = fields.Char(string="Plan")
    op_cost_per_month = fields.Float(string="Cost Per Month")  # better numeric
    op_center = fields.Char(string="Center")
    op_sales_person = fields.Char(string="Sales Person")
    op_contact_number = fields.Char(string="Contact Number")
    op_email = fields.Char(string="Email")
    op_notes = fields.Text(string="Notes")   # changed to Text
    op_dnc_ref_no = fields.Char(string="DNC Reference No")
    op_audit_1 = fields.Char(string="Audit 1")
    op_audit_2 = fields.Char(string="Audit 2")       


    @api.model
    def _save_optus_nbn_data(self):
        """
        Save Optus BNB form data per stage in custom.optus.nbn.form
        """
        for lead in self:
            stage = lead.optus_form_stage
            if not stage:
                continue

            OptusBNBForm = self.env['custom.optus.nbn.form']

            # Check if record for this lead and stage exists
            existing = OptusBNBForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            op_vals = {
                'lead_id': lead.id,
                'stage': stage,
                'sale_date': lead.op_sale_date,
                'activation_date': lead.op_activation_date,
                'order_no': lead.op_order_no,
                'customer_name': lead.op_customer_name,
                'service_address': lead.op_service_address,
                'service': lead.op_service,
                'plan': lead.op_plan,
                'cost_per_month': lead.op_cost_per_month,
                'center': lead.op_center,
                'sales_person': lead.op_sales_person,
                'contact_number': lead.op_contact_number,
                'email': lead.op_email,
                'notes': lead.op_notes,
                'dnc_ref_no': lead.op_dnc_ref_no,
                'audit_1': lead.op_audit_1,
                'audit_2': lead.op_audit_2,
            }

            if existing:
                existing.write(op_vals)
            else:
                OptusBNBForm.create(op_vals)

    @api.onchange('optus_form_stage')
    def _onchange_optus_form_stage(self):
        """
        Load Optus BNB form data from saved stage when user changes stage
        """
        for rec in self:
            if not rec.optus_form_stage:
                return

            OptusBNBForm = self.env['custom.optus.nbn.form']
            existing = OptusBNBForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.optus_form_stage)
            ], limit=1)

            if existing:
                rec.op_sale_date = existing.sale_date
                rec.op_activation_date = existing.activation_date
                rec.op_order_no = existing.order_no
                rec.op_customer_name = existing.customer_name
                rec.op_service_address = existing.service_address
                rec.op_service = existing.service
                rec.op_plan = existing.plan
                rec.op_cost_per_month = existing.cost_per_month
                rec.op_center = existing.center
                rec.op_sales_person = existing.sales_person
                rec.op_contact_number = existing.contact_number
                rec.op_email = existing.email
                rec.op_notes = existing.notes
                rec.op_dnc_ref_no = existing.dnc_ref_no
                rec.op_audit_1 = existing.audit_1
                rec.op_audit_2 = existing.audit_2
            else:
                # Reset fields if no existing data is found
                rec.op_sale_date = False
                rec.op_activation_date = False
                rec.op_order_no = False
                rec.op_customer_name = False
                rec.op_service_address = False
                rec.op_service = False
                rec.op_plan = False
                rec.op_cost_per_month = 0.0
                rec.op_center = False
                rec.op_sales_person = False
                rec.op_contact_number = rec.phone_sanitized or False  # default from lead
                rec.op_email = rec.email_normalized or False          # default from lead
                rec.op_notes = False
                rec.op_dnc_ref_no = False
                rec.op_audit_1 = False
                rec.op_audit_2 = False     


    # FIRST ENERGY FORM
    first_energy_form_stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='First Energy Stage', default="1")
    fe_internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    fe_existing_sale = fields.Char(string="Existing Sale with NMI & Phone Number")
    fe_online_enquiry_form = fields.Char(string="Online Enquiry Form")
    fe_vendor_id = fields.Char(string="Vendor ID")
    fe_agent = fields.Char(string="Agent")
    fe_channel_ref = fields.Char(string="Channel Reference")
    fe_sale_ref = fields.Char(string="Sale Reference")
    fe_lead_ref = fields.Char(string="Lead Ref (External)")  # renamed to avoid clash
    fe_incentive = fields.Char(string="Incentive")
    fe_sale_date = fields.Date(string="Date of Sale")
    fe_campaign_ref = fields.Char(string="Campaign Reference")
    fe_promo_code = fields.Char(string="Promo Code")
    fe_current_elec_retailer = fields.Char(string="Current Electric Retailer")
    fe_current_gas_retailer = fields.Char(string="Current Gas Retailer")
    fe_multisite = fields.Boolean(string="Multisite")
    fe_existing_customer = fields.Boolean(string="Existing Customer")
    fe_customer_account_no = fields.Char(string="Customer Account Number")
    fe_customer_type = fields.Selection([
        ('resident', 'Resident'),
        ('company', 'Company'),
    ], string='Customer Type', default="resident")
    fe_account_name = fields.Char(string="Account Name")
    fe_abn = fields.Char(string="ABN")
    fe_acn = fields.Char(string="ACN")
    fe_business_name = fields.Char(string="Business Name")
    fe_trustee_name = fields.Char(string="Trustee Name")
    fe_trading_name = fields.Char(string="Trading Name")
    fe_position = fields.Char(string="Position")
    fe_sale_type = fields.Selection([
        ('transfer', 'Transfer'),
        ('movein', 'Movein')
    ], string="Sale Type", default="transfer")
    fe_title = fields.Char(string="Title")
    fe_first_name = fields.Char(string="First Name")
    fe_last_name = fields.Char(string="Last Name")
    fe_phone_landline = fields.Char(string="Phone Landline")
    fe_phone_mobile = fields.Char(string="Mobile Number")
    fe_auth_date_of_birth = fields.Date(string="Authentication Date of Birth")
    fe_auth_expiry = fields.Date(string="Authentication Expiry")
    fe_auth_no = fields.Char(string="Authentication No")
    fe_auth_type = fields.Char(string="Authentication Type")
    fe_email = fields.Char(string="Email")
    fe_life_support = fields.Boolean(string="Life Support", default=False)
    fe_concessioner_number = fields.Char(string="Concessioner Number")
    fe_concession_expiry = fields.Date(string="Concession Expiry Date")
    fe_concession_flag = fields.Boolean(string="Concession Flag", default=False)
    fe_concession_start_date = fields.Date(string="Concession Start Date")
    fe_concession_type = fields.Char(string="Concession Type")
    fe_conc_first_name = fields.Char(string="Concession First Name")
    fe_conc_last_name = fields.Char(string="Concession Last Name")
    fe_secondary_title = fields.Char(string="Secondary Title")
    fe_sec_first_name = fields.Char(string="Secondary First Name")
    fe_sec_last_name = fields.Char(string="Secondary Last Name")
    fe_sec_auth_date_of_birth = fields.Date(string="Secondary Authentication DOB")
    fe_sec_auth_no = fields.Char(string="Secondary Authentication No")
    fe_sec_auth_type = fields.Char(string="Secondary Authentication Type")
    fe_sec_auth_expiry = fields.Date(string="Secondary Authentication Expiry")
    fe_sec_email = fields.Char(string="Secondary Email")
    fe_sec_phone_home = fields.Char(string="Secondary Phone Home")
    fe_sec_mobile_number = fields.Char(string="Secondary Mobile Number")
    fe_site_apartment_no = fields.Char(string="Site Apartment Number")
    fe_site_apartment_type = fields.Char(string="Site Apartment Type")
    fe_site_building_name = fields.Char(string="Site Building Name")
    fe_site_floor_no = fields.Char(string="Site Floor Number")
    fe_site_floor_type = fields.Char(string="Site Floor Type")
    fe_site_location_description = fields.Text(string="Site Location Description")
    fe_site_lot_number = fields.Char(string="Site Lot Number")
    fe_site_street_number = fields.Char(string="Site Street Number")
    fe_site_street_name = fields.Char(string="Site Street Name")
    fe_site_street_number_suffix = fields.Char(string="Site Street Number Suffix")
    fe_site_street_type = fields.Char(string="Site Street Type")
    fe_site_street_suffix = fields.Char(string="Site Street Suffix")
    fe_site_suburb = fields.Char(string="Site Suburb")
    fe_site_state = fields.Char(string="Site State")
    fe_site_post_code = fields.Char(string="Site Post Code")
    fe_gas_site_apartment_number = fields.Char(string="Gas Site Apartment Number")
    fe_gas_site_apartment_type = fields.Char(string="Gas Site Apartment Type")
    fe_gas_site_building_name = fields.Char(string="Gas Site Building Name")
    fe_gas_site_floor_number = fields.Char(string="Gas Site Floor Number")
    fe_gas_site_floor_type = fields.Char(string="Gas Site Floor Type")
    fe_gas_site_location_description = fields.Char(string="Gas Site Location Description")
    fe_gas_site_lot_number = fields.Char(string="Gas Site Lot Number")
    fe_gas_site_street_name = fields.Char(string="Gas Site Street Name")
    fe_gas_site_street_number = fields.Char(string="Gas Site Street Number")
    fe_gas_site_street_number_suffix = fields.Char(string="Gas Site Street Number Suffix")  # typo fixed
    fe_gas_site_street_type = fields.Char(string="Gas Site Street Type")
    fe_gas_site_street_suffix = fields.Char("Gas Site Street Suffix")
    fe_gas_site_suburb = fields.Char("Gas Site Suburb")
    fe_gas_site_state = fields.Char("Gas Site State")
    fe_gas_site_post_code = fields.Char("Gas Site Post Code")
    fe_network_tariff_code = fields.Char("Network Tariff Code")
    fe_nmi = fields.Char("NMI")
    fe_mirn = fields.Char("MIRN")
    fe_fuel = fields.Char("Fuel")
    fe_feed_in = fields.Char("Feed In")
    fe_annual_usage = fields.Float("Annual Usage")
    fe_gas_annual_usage = fields.Float("Gas Annual Usage")
    fe_product_code = fields.Char("Product Code")
    fe_gas_product_code = fields.Char("Gas Product Code")
    fe_offer_description = fields.Text("Offer Description")
    fe_gas_offer_description = fields.Text("Gas Offer Description")
    fe_green_percent = fields.Float("Green Percent")
    fe_proposed_transfer_date = fields.Date("Proposed Transfer Date")
    fe_gas_proposed_transfer_date = fields.Date("Gas Proposed Transfer Date")
    fe_bill_cycle_code = fields.Char("Bill Cycle Code")
    fe_gas_bill_cycle_code = fields.Char("Gas Bill Cycle Code")
    fe_average_monthly_spend = fields.Float("Average Monthly Spend")
    fe_is_owner = fields.Boolean("Is Owner")
    fe_has_accepted_marketing = fields.Boolean("Has Accepted Marketing")
    fe_email_account_notice = fields.Boolean("Email Account Notice")
    fe_email_invoice = fields.Boolean("Email Invoice")
    fe_billing_email = fields.Char("Billing Email")
    fe_postal_building_name = fields.Char("Postal Building Name")
    fe_postal_apartment_number = fields.Char("Postal Apartment Number")
    fe_postal_apartment_type = fields.Char("Postal Apartment Type")
    fe_postal_floor_number = fields.Char("Postal Floor Number")
    fe_postal_floor_type = fields.Char("Postal Floor Type")
    fe_postal_lot_no = fields.Char("Postal Lot No")
    fe_postal_street_number = fields.Char("Postal Street Number")
    fe_postal_street_number_suffix = fields.Char("Postal Street Number Suffix")
    fe_postal_street_name = fields.Char("Postal Street Name")
    fe_postal_street_type = fields.Char("Postal Street Type")
    fe_postal_street_suffix = fields.Char("Postal Street Suffix")
    fe_postal_suburb = fields.Char("Postal Suburb")
    fe_postal_post_code = fields.Char("Postal Post Code")
    fe_postal_state = fields.Char("Postal State")
    fe_comments = fields.Text("Comments")
    fe_transfer_special_instructions = fields.Text("Transfer Special Instructions")
    fe_medical_cooling = fields.Boolean("Medical Cooling")
    fe_medical_cooling_energy_rebate = fields.Boolean("Medical Cooling Energy Rebate")
    fe_benefit_end_date = fields.Date("Benefit End Date")
    fe_sales_class = fields.Char("Sales Class")
    fe_bill_group_code = fields.Char("Bill Group Code")
    fe_gas_meter_number = fields.Char("Gas Meter Number")
    fe_centre_name = fields.Char("Centre Name")
    fe_qc_name = fields.Char("QC Name")
    fe_verifiers_name = fields.Char("Verifier’s Name")
    fe_tl_name = fields.Char("TL Name")
    fe_dnc_ref_no = fields.Char("DNC Ref No")
    fe_audit_2 = fields.Char("Audit-2")
    fe_welcome_call = fields.Boolean("Welcome Call")    


    @api.model
    def _save_first_energy_data(self):
        """
        Save First Energy form data per stage into custom.first.energy.form.
        Looks up by (lead_id, stage) and writes or creates a record.
        """
        FirstEnergyForm = self.env['custom.first.energy.form']

        for lead in self:
            stage = lead.first_energy_form_stage
            if not stage:
                continue

            existing = FirstEnergyForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            fe_vals = {
                'lead_id': lead.id,
                'stage': stage,

                # Header / meta
                'internal_dnc_checked': lead.fe_internal_dnc_checked,
                'existing_sale': lead.fe_existing_sale,
                'online_enquiry_form': lead.fe_online_enquiry_form,
                'vendor_id': lead.fe_vendor_id,
                'agent': lead.fe_agent,
                'channel_ref': lead.fe_channel_ref,
                'sale_ref': lead.fe_sale_ref,
                'lead_ref': lead.fe_lead_ref,
                'incentive': lead.fe_incentive,
                'sale_date': lead.fe_sale_date,
                'campaign_ref': lead.fe_campaign_ref,
                'promo_code': lead.fe_promo_code,

                # Current retailers / flags
                'current_elec_retailer': lead.fe_current_elec_retailer,
                'current_gas_retailer': lead.fe_current_gas_retailer,
                'multisite': lead.fe_multisite,
                'existing_customer': lead.fe_existing_customer,
                'customer_account_no': lead.fe_customer_account_no,

                # Customer / business identity
                'customer_type': lead.fe_customer_type,
                'account_name': lead.fe_account_name,
                'abn': lead.fe_abn,
                'acn': lead.fe_acn,
                'business_name': lead.fe_business_name,
                'trustee_name': lead.fe_trustee_name,
                'trading_name': lead.fe_trading_name,
                'position': lead.fe_position,
                'sale_type': lead.fe_sale_type,

                # Primary contact / auth
                'title': lead.fe_title,
                'first_name': lead.fe_first_name,
                'last_name': lead.fe_last_name,
                'phone_landline': lead.fe_phone_landline,
                'phone_mobile': lead.fe_phone_mobile,
                'auth_date_of_birth': lead.fe_auth_date_of_birth,
                'auth_expiry': lead.fe_auth_expiry,
                'auth_no': lead.fe_auth_no,
                'auth_type': lead.fe_auth_type,
                'email': lead.fe_email,
                'life_support': lead.fe_life_support,

                # Concession
                'concessioner_number': lead.fe_concessioner_number,
                'concession_expiry': lead.fe_concession_expiry,
                'concession_flag': lead.fe_concession_flag,
                'concession_start_date': lead.fe_concession_start_date,
                'concession_type': lead.fe_concession_type,
                'conc_first_name': lead.fe_conc_first_name,
                'conc_last_name': lead.fe_conc_last_name,

                # Secondary contact
                'secondary_title': lead.fe_secondary_title,
                'sec_first_name': lead.fe_sec_first_name,
                'sec_last_name': lead.fe_sec_last_name,
                'sec_auth_date_of_birth': lead.fe_sec_auth_date_of_birth,
                'sec_auth_no': lead.fe_sec_auth_no,
                'sec_auth_type': lead.fe_sec_auth_type,
                'sec_auth_expiry': lead.fe_sec_auth_expiry,
                'sec_email': lead.fe_sec_email,
                'sec_phone_home': lead.fe_sec_phone_home,
                'sec_mobile_number': lead.fe_sec_mobile_number,

                # Electricity site address
                'site_apartment_no': lead.fe_site_apartment_no,
                'site_apartment_type': lead.fe_site_apartment_type,
                'site_building_name': lead.fe_site_building_name,
                'site_floor_no': lead.fe_site_floor_no,
                'site_floor_type': lead.fe_site_floor_type,
                'site_location_description': lead.fe_site_location_description,
                'site_lot_number': lead.fe_site_lot_number,
                'site_street_number': lead.fe_site_street_number,
                'site_street_name': lead.fe_site_street_name,
                'site_street_number_suffix': lead.fe_site_street_number_suffix,
                'site_street_type': lead.fe_site_street_type,
                'site_street_suffix': lead.fe_site_street_suffix,
                'site_suburb': lead.fe_site_suburb,
                'site_state': lead.fe_site_state,
                'site_post_code': lead.fe_site_post_code,

                # Gas site address
                'gas_site_apartment_number': lead.fe_gas_site_apartment_number,
                'gas_site_apartment_type': lead.fe_gas_site_apartment_type,
                'gas_site_building_name': lead.fe_gas_site_building_name,
                'gas_site_floor_number': lead.fe_gas_site_floor_number,
                'gas_site_floor_type': lead.fe_gas_site_floor_type,
                'gas_site_location_description': lead.fe_gas_site_location_description,
                'gas_site_lot_number': lead.fe_gas_site_lot_number,
                'gas_site_street_name': lead.fe_gas_site_street_name,
                'gas_site_street_number': lead.fe_gas_site_street_number,
                'gas_site_street_number_suffix': lead.fe_gas_site_street_number_suffix,
                'gas_site_street_type': lead.fe_gas_site_street_type,
                'gas_site_street_suffix': lead.fe_gas_site_street_suffix,
                'gas_site_suburb': lead.fe_gas_site_suburb,
                'gas_site_state': lead.fe_gas_site_state,
                'gas_site_post_code': lead.fe_gas_site_post_code,

                # Metering / products / usage
                'network_tariff_code': lead.fe_network_tariff_code,
                'nmi': lead.fe_nmi,
                'mirn': lead.fe_mirn,
                'fuel': lead.fe_fuel,
                'feed_in': lead.fe_feed_in,
                'annual_usage': lead.fe_annual_usage,
                'gas_annual_usage': lead.fe_gas_annual_usage,
                'product_code': lead.fe_product_code,
                'gas_product_code': lead.fe_gas_product_code,
                'offer_description': lead.fe_offer_description,
                'gas_offer_description': lead.fe_gas_offer_description,
                'green_percent': lead.fe_green_percent,
                'proposed_transfer_date': lead.fe_proposed_transfer_date,
                'gas_proposed_transfer_date': lead.fe_gas_proposed_transfer_date,
                'bill_cycle_code': lead.fe_bill_cycle_code,
                'gas_bill_cycle_code': lead.fe_gas_bill_cycle_code,
                'average_monthly_spend': lead.fe_average_monthly_spend,

                # Ownership / comms prefs
                'is_owner': lead.fe_is_owner,
                'has_accepted_marketing': lead.fe_has_accepted_marketing,
                'email_account_notice': lead.fe_email_account_notice,
                'email_invoice': lead.fe_email_invoice,
                'billing_email': lead.fe_billing_email,

                # Postal
                'postal_building_name': lead.fe_postal_building_name,
                'postal_apartment_number': lead.fe_postal_apartment_number,
                'postal_apartment_type': lead.fe_postal_apartment_type,
                'postal_floor_number': lead.fe_postal_floor_number,
                'postal_floor_type': lead.fe_postal_floor_type,
                'postal_lot_no': lead.fe_postal_lot_no,
                'postal_street_number': lead.fe_postal_street_number,
                'postal_street_number_suffix': lead.fe_postal_street_number_suffix,
                'postal_street_name': lead.fe_postal_street_name,
                'postal_street_type': lead.fe_postal_street_type,
                'postal_street_suffix': lead.fe_postal_street_suffix,
                'postal_suburb': lead.fe_postal_suburb,
                'postal_post_code': lead.fe_postal_post_code,
                'postal_state': lead.fe_postal_state,

                # Notes / special / rebates
                'comments': lead.fe_comments,
                'transfer_special_instructions': lead.fe_transfer_special_instructions,
                'medical_cooling': lead.fe_medical_cooling,
                'medical_cooling_energy_rebate': lead.fe_medical_cooling_energy_rebate,
                'benefit_end_date': lead.fe_benefit_end_date,

                # Ops
                'sales_class': lead.fe_sales_class,
                'bill_group_code': lead.fe_bill_group_code,
                'gas_meter_number': lead.fe_gas_meter_number,
                'centre_name': lead.fe_centre_name,
                'qc_name': lead.fe_qc_name,
                'verifiers_name': lead.fe_verifiers_name,
                'tl_name': lead.fe_tl_name,
                'dnc_ref_no': lead.fe_dnc_ref_no,
                'audit_2': lead.fe_audit_2,
                'welcome_call': lead.fe_welcome_call,
            }

            if existing:
                existing.write(fe_vals)
            else:
                FirstEnergyForm.create(fe_vals)  

    @api.onchange('first_energy_form_stage')
    def _onchange_first_energy_form_stage(self):
        """
        Load First Energy form data from saved stage when user changes stage
        """
        for rec in self:
            if not rec.first_energy_form_stage:
                return

            FirstEnergyForm = self.env['custom.first.energy.form']
            existing = FirstEnergyForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.first_energy_form_stage)
            ], limit=1)

            if existing:
                rec.fe_internal_dnc_checked = existing.internal_dnc_checked
                rec.fe_existing_sale = existing.existing_sale
                rec.fe_online_enquiry_form = existing.online_enquiry_form
                rec.fe_vendor_id = existing.vendor_id
                rec.fe_agent = existing.agent
                rec.fe_channel_ref = existing.channel_ref
                rec.fe_sale_ref = existing.sale_ref
                rec.fe_lead_ref = existing.lead_ref
                rec.fe_incentive = existing.incentive
                rec.fe_sale_date = existing.sale_date
                rec.fe_campaign_ref = existing.campaign_ref
                rec.fe_promo_code = existing.promo_code
                rec.fe_current_elec_retailer = existing.current_elec_retailer
                rec.fe_current_gas_retailer = existing.current_gas_retailer
                rec.fe_multisite = existing.multisite
                rec.fe_existing_customer = existing.existing_customer
                rec.fe_customer_account_no = existing.customer_account_no
                rec.fe_customer_type = existing.customer_type
                rec.fe_account_name = existing.account_name
                rec.fe_abn = existing.abn
                rec.fe_acn = existing.acn
                rec.fe_business_name = existing.business_name
                rec.fe_trustee_name = existing.trustee_name
                rec.fe_trading_name = existing.trading_name
                rec.fe_position = existing.position
                rec.fe_sale_type = existing.sale_type
                rec.fe_title = existing.title
                rec.fe_first_name = existing.first_name
                rec.fe_last_name = existing.last_name
                rec.fe_phone_landline = existing.phone_landline
                rec.fe_phone_mobile = existing.phone_mobile
                rec.fe_auth_date_of_birth = existing.auth_date_of_birth
                rec.fe_auth_expiry = existing.auth_expiry
                rec.fe_auth_no = existing.auth_no
                rec.fe_auth_type = existing.auth_type
                rec.fe_email = existing.email
                rec.fe_life_support = existing.life_support
                rec.fe_concessioner_number = existing.concessioner_number
                rec.fe_concession_expiry = existing.concession_expiry
                rec.fe_concession_flag = existing.concession_flag
                rec.fe_concession_start_date = existing.concession_start_date
                rec.fe_concession_type = existing.concession_type
                rec.fe_conc_first_name = existing.conc_first_name
                rec.fe_conc_last_name = existing.conc_last_name
                rec.fe_secondary_title = existing.secondary_title
                rec.fe_sec_first_name = existing.sec_first_name
                rec.fe_sec_last_name = existing.sec_last_name
                rec.fe_sec_auth_date_of_birth = existing.sec_auth_date_of_birth
                rec.fe_sec_auth_no = existing.sec_auth_no
                rec.fe_sec_auth_type = existing.sec_auth_type
                rec.fe_sec_auth_expiry = existing.sec_auth_expiry
                rec.fe_sec_email = existing.sec_email
                rec.fe_sec_phone_home = existing.sec_phone_home
                rec.fe_sec_mobile_number = existing.sec_mobile_number
                rec.fe_site_apartment_no = existing.site_apartment_no
                rec.fe_site_apartment_type = existing.site_apartment_type
                rec.fe_site_building_name = existing.site_building_name
                rec.fe_site_floor_no = existing.site_floor_no
                rec.fe_site_floor_type = existing.site_floor_type
                rec.fe_site_location_description = existing.site_location_description
                rec.fe_site_lot_number = existing.site_lot_number
                rec.fe_site_street_number = existing.site_street_number
                rec.fe_site_street_name = existing.site_street_name
                rec.fe_site_street_number_suffix = existing.site_street_number_suffix
                rec.fe_site_street_type = existing.site_street_type
                rec.fe_site_street_suffix = existing.site_street_suffix
                rec.fe_site_suburb = existing.site_suburb
                rec.fe_site_state = existing.site_state
                rec.fe_site_post_code = existing.site_post_code
                rec.fe_gas_site_apartment_number = existing.gas_site_apartment_number
                rec.fe_gas_site_apartment_type = existing.gas_site_apartment_type
                rec.fe_gas_site_building_name = existing.gas_site_building_name
                rec.fe_gas_site_floor_number = existing.gas_site_floor_number
                rec.fe_gas_site_floor_type = existing.gas_site_floor_type
                rec.fe_gas_site_location_description = existing.gas_site_location_description
                rec.fe_gas_site_lot_number = existing.gas_site_lot_number
                rec.fe_gas_site_street_name = existing.gas_site_street_name
                rec.fe_gas_site_street_number = existing.gas_site_street_number
                rec.fe_gas_site_street_number_suffix = existing.gas_site_street_number_suffix
                rec.fe_gas_site_street_type = existing.gas_site_street_type
                rec.fe_gas_site_street_suffix = existing.gas_site_street_suffix
                rec.fe_gas_site_suburb = existing.gas_site_suburb
                rec.fe_gas_site_state = existing.gas_site_state
                rec.fe_gas_site_post_code = existing.gas_site_post_code
                rec.fe_network_tariff_code = existing.network_tariff_code
                rec.fe_nmi = existing.nmi
                rec.fe_mirn = existing.mirn
                rec.fe_fuel = existing.fuel
                rec.fe_feed_in = existing.feed_in
                rec.fe_annual_usage = existing.annual_usage
                rec.fe_gas_annual_usage = existing.gas_annual_usage
                rec.fe_product_code = existing.product_code
                rec.fe_gas_product_code = existing.gas_product_code
                rec.fe_offer_description = existing.offer_description
                rec.fe_gas_offer_description = existing.gas_offer_description
                rec.fe_green_percent = existing.green_percent
                rec.fe_proposed_transfer_date = existing.proposed_transfer_date
                rec.fe_gas_proposed_transfer_date = existing.gas_proposed_transfer_date
                rec.fe_bill_cycle_code = existing.bill_cycle_code
                rec.fe_gas_bill_cycle_code = existing.gas_bill_cycle_code
                rec.fe_average_monthly_spend = existing.average_monthly_spend
                rec.fe_is_owner = existing.is_owner
                rec.fe_has_accepted_marketing = existing.has_accepted_marketing
                rec.fe_email_account_notice = existing.email_account_notice
                rec.fe_email_invoice = existing.email_invoice
                rec.fe_billing_email = existing.billing_email
                rec.fe_postal_building_name = existing.postal_building_name
                rec.fe_postal_apartment_number = existing.postal_apartment_number
                rec.fe_postal_apartment_type = existing.postal_apartment_type
                rec.fe_postal_floor_number = existing.postal_floor_number
                rec.fe_postal_floor_type = existing.postal_floor_type
                rec.fe_postal_lot_no = existing.postal_lot_no
                rec.fe_postal_street_number = existing.postal_street_number
                rec.fe_postal_street_number_suffix = existing.postal_street_number_suffix
                rec.fe_postal_street_name = existing.postal_street_name
                rec.fe_postal_street_type = existing.postal_street_type
                rec.fe_postal_street_suffix = existing.postal_street_suffix
                rec.fe_postal_suburb = existing.postal_suburb
                rec.fe_postal_post_code = existing.postal_post_code
                rec.fe_postal_state = existing.postal_state
                rec.fe_comments = existing.comments
                rec.fe_transfer_special_instructions = existing.transfer_special_instructions
                rec.fe_medical_cooling = existing.medical_cooling
                rec.fe_medical_cooling_energy_rebate = existing.medical_cooling_energy_rebate
                rec.fe_benefit_end_date = existing.benefit_end_date
                rec.fe_sales_class = existing.sales_class
                rec.fe_bill_group_code = existing.bill_group_code
                rec.fe_gas_meter_number = existing.gas_meter_number
                rec.fe_centre_name = existing.centre_name
                rec.fe_qc_name = existing.qc_name
                rec.fe_verifiers_name = existing.verifiers_name
                rec.fe_tl_name = existing.tl_name
                rec.fe_dnc_ref_no = existing.dnc_ref_no
                rec.fe_audit_2 = existing.audit_2
                rec.fe_welcome_call = existing.welcome_call

            else:
                # Reset fields if no existing data is found
                rec.fe_internal_dnc_checked = False
                rec.fe_existing_sale = False
                rec.fe_online_enquiry_form = False
                rec.fe_vendor_id = False
                rec.fe_agent = False
                rec.fe_channel_ref = False
                rec.fe_sale_ref = False
                rec.fe_lead_ref = False
                rec.fe_incentive = False
                rec.fe_sale_date = False
                rec.fe_campaign_ref = False
                rec.fe_promo_code = False
                rec.fe_current_elec_retailer = False
                rec.fe_current_gas_retailer = False
                rec.fe_multisite = False
                rec.fe_existing_customer = False
                rec.fe_customer_account_no = False
                rec.fe_customer_type = False
                rec.fe_account_name = False
                rec.fe_abn = False
                rec.fe_acn = False
                rec.fe_business_name = False
                rec.fe_trustee_name = False
                rec.fe_trading_name = False
                rec.fe_position = False
                rec.fe_sale_type = False
                rec.fe_title = False
                rec.fe_first_name = False
                rec.fe_last_name = False
                rec.fe_phone_landline = False
                rec.fe_phone_mobile = rec.phone_sanitized or False   # default from lead
                rec.fe_auth_date_of_birth = False
                rec.fe_auth_expiry = False
                rec.fe_auth_no = False
                rec.fe_auth_type = False
                rec.fe_email = rec.email_normalized or False         # default from lead
                rec.fe_life_support = False
                rec.fe_concessioner_number = False
                rec.fe_concession_expiry = False
                rec.fe_concession_flag = False
                rec.fe_concession_start_date = False
                rec.fe_concession_type = False
                rec.fe_conc_first_name = False
                rec.fe_conc_last_name = False
                rec.fe_secondary_title = False
                rec.fe_sec_first_name = False
                rec.fe_sec_last_name = False
                rec.fe_sec_auth_date_of_birth = False
                rec.fe_sec_auth_no = False
                rec.fe_sec_auth_type = False
                rec.fe_sec_auth_expiry = False
                rec.fe_sec_email = False
                rec.fe_sec_phone_home = False
                rec.fe_sec_mobile_number = False
                rec.fe_site_apartment_no = False
                rec.fe_site_apartment_type = False
                rec.fe_site_building_name = False
                rec.fe_site_floor_no = False
                rec.fe_site_floor_type = False
                rec.fe_site_location_description = False
                rec.fe_site_lot_number = False
                rec.fe_site_street_number = False
                rec.fe_site_street_name = False
                rec.fe_site_street_number_suffix = False
                rec.fe_site_street_type = False
                rec.fe_site_street_suffix = False
                rec.fe_site_suburb = False
                rec.fe_site_state = False
                rec.fe_site_post_code = False
                rec.fe_gas_site_apartment_number = False
                rec.fe_gas_site_apartment_type = False
                rec.fe_gas_site_building_name = False
                rec.fe_gas_site_floor_number = False
                rec.fe_gas_site_floor_type = False
                rec.fe_gas_site_location_description = False
                rec.fe_gas_site_lot_number = False
                rec.fe_gas_site_street_name = False
                rec.fe_gas_site_street_number = False
                rec.fe_gas_site_street_number_suffix = False
                rec.fe_gas_site_street_type = False
                rec.fe_gas_site_street_suffix = False
                rec.fe_gas_site_suburb = False
                rec.fe_gas_site_state = False
                rec.fe_gas_site_post_code = False
                rec.fe_network_tariff_code = False
                rec.fe_nmi = False
                rec.fe_mirn = False
                rec.fe_fuel = False
                rec.fe_feed_in = False
                rec.fe_annual_usage = 0.0
                rec.fe_gas_annual_usage = 0.0
                rec.fe_product_code = False
                rec.fe_gas_product_code = False
                rec.fe_offer_description = False
                rec.fe_gas_offer_description = False
                rec.fe_green_percent = 0.0
                rec.fe_proposed_transfer_date = False
                rec.fe_gas_proposed_transfer_date = False
                rec.fe_bill_cycle_code = False
                rec.fe_gas_bill_cycle_code = False
                rec.fe_average_monthly_spend = 0.0
                rec.fe_is_owner = False
                rec.fe_has_accepted_marketing = False
                rec.fe_email_account_notice = False
                rec.fe_email_invoice = False
                rec.fe_billing_email = False
                rec.fe_postal_building_name = False
                rec.fe_postal_apartment_number = False
                rec.fe_postal_apartment_type = False
                rec.fe_postal_floor_number = False
                rec.fe_postal_floor_type = False
                rec.fe_postal_lot_no = False
                rec.fe_postal_street_number = False
                rec.fe_postal_street_number_suffix = False
                rec.fe_postal_street_name = False
                rec.fe_postal_street_type = False
                rec.fe_postal_street_suffix = False
                rec.fe_postal_suburb = False
                rec.fe_postal_post_code = False
                rec.fe_postal_state = False
                rec.fe_comments = False
                rec.fe_transfer_special_instructions = False
                rec.fe_medical_cooling = False
                rec.fe_medical_cooling_energy_rebate = False
                rec.fe_benefit_end_date = False
                rec.fe_sales_class = False
                rec.fe_bill_group_code = False
                rec.fe_gas_meter_number = False
                rec.fe_centre_name = False
                rec.fe_qc_name = False
                rec.fe_verifiers_name = False
                rec.fe_tl_name = False
                rec.fe_dnc_ref_no = False
                rec.fe_audit_2 = False
                rec.fe_welcome_call = False


#    DODO POWER AND GAS FORM
    dodo_power_stage = fields.Selection([
        ('1', 'Stage 1'),
        ('2', 'Stage 2'),
        ('3', 'Stage 3'),
        ('4', 'Stage 4'),
        ('5', 'Stage 5')
    ], string='DODO Power Stage', default="1")

    # Compliance / Internal
    dp_internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    dp_existing_sale = fields.Char(string="Existing Sale with NMI & Phone Number (Internal)")
    dp_online_enquiry_form = fields.Char(string="Online Enquiry Form")

    # Sales Info
    dp_sales_name = fields.Char(string="Sales Name")
    dp_sales_reference = fields.Char(string="Sales Reference")
    dp_agreement_date = fields.Date(string="Agreement Date")

    # Site / Address
    dp_site_address_postcode = fields.Char(string="Site Address Postcode")
    dp_site_addr_unit_type = fields.Char(string="Site Addr Unit Type")
    dp_site_addr_unit_no = fields.Char(string="Site Addr Unit No")
    dp_site_addr_floor_type = fields.Char(string="Site Addr Floor Type")
    dp_site_addr_floor_no = fields.Char(string="Site Addr Floor No")
    dp_site_addr_street_no = fields.Char(string="Site Addr Street No")
    dp_site_addr_street_no_suffix = fields.Char(string="Site Addr Street No Suffix")
    dp_site_addr_street_name = fields.Char(string="Site Addr Street Name")
    dp_site_addr_street_type = fields.Char(string="Site Addr Street Type")
    dp_site_addr_suburb = fields.Char(string="Site Addr Suburb")
    dp_site_addr_state = fields.Char(string="Site Addr State")
    dp_site_addr_postcode = fields.Char(string="Site Addr Postcode")
    dp_site_addr_desc = fields.Text(string="Site Address Description")
    dp_site_access = fields.Text(string="Site Access")
    dp_site_more_than_12_months = fields.Boolean(string="At Site > 12 Months")

    # Previous Address
    dp_prev_addr_1 = fields.Char(string="Previous Address Line 1")
    dp_prev_addr_2 = fields.Char(string="Previous Address Line 2")
    dp_prev_addr_state = fields.Char(string="Previous Address State")
    dp_prev_addr_postcode = fields.Char(string="Previous Address Postcode")

    # Billing Address
    dp_billing_address = fields.Boolean(string="Billing Address")
    dp_bill_addr_1 = fields.Char(string="Bill Address Line 1")
    dp_bill_addr_2 = fields.Char(string="Bill Address Line 2")
    dp_bill_addr_state = fields.Char(string="Bill Address State")
    dp_bill_addr_postcode = fields.Char(string="Bill Address Postcode")

    # Concessions
    dp_concession = fields.Boolean(string="Concession")
    dp_concession_card_type = fields.Char(string="Concession Card Type")
    dp_concession_card_no = fields.Char(string="Concession Card No")
    dp_concession_start_date = fields.Date(string="Concession Start Date")
    dp_concession_exp_date = fields.Date(string="Concession Expiry Date")
    dp_concession_first_name = fields.Char(string="Concession First Name")
    dp_concession_middle_name = fields.Char(string="Concession Middle Name")
    dp_concession_last_name = fields.Char(string="Concession Last Name")

    # Product / Energy Details
    dp_product_code = fields.Char(string="Product Code")
    dp_meter_type = fields.Char(string="Meter Type")
    dp_kwh_usage_per_day = fields.Float(string="kWh Usage Per Day")
    dp_how_many_people = fields.Integer(string="Number of People")
    dp_how_many_bedrooms = fields.Integer(string="Number of Bedrooms")
    dp_solar_power = fields.Boolean(string="Solar Power")
    dp_solar_type = fields.Char(string="Solar Type")
    dp_solar_output = fields.Float(string="Solar Output")
    dp_green_energy = fields.Boolean(string="Green Energy")
    dp_winter_gas_usage = fields.Float(string="Winter Gas Usage")
    dp_summer_gas_usage = fields.Float(string="Summer Gas Usage")
    dp_monthly_winter_spend = fields.Float(string="Monthly Winter Spend")
    dp_monthly_summer_spend = fields.Float(string="Monthly Summer Spend")

    # Invoice
    dp_invoice_method = fields.Selection([
        ('email', 'Email'),
        ('post', 'Post'),
        ('sms', 'SMS')
    ], string="Invoice Method")

    # Customer Info
    dp_customer_salutation = fields.Char(string="Customer Salutation")
    dp_first_name = fields.Char(string="First Name")
    dp_last_name = fields.Char(string="Last Name")
    dp_date_of_birth = fields.Date(string="Date of Birth")
    dp_email_contact = fields.Char(string="Email Contact")
    dp_contact_number = fields.Char(string="Contact Number")
    dp_hearing_impaired = fields.Boolean(string="Hearing Impaired", default=False)

    # Secondary Contact
    dp_secondary_contact = fields.Boolean(string="Secondary Contact", default=False)
    dp_secondary_salutation = fields.Char(string="Secondary Salutation")
    dp_secondary_first_name = fields.Char(string="Secondary First Name")
    dp_secondary_last_name = fields.Char(string="Secondary Last Name")
    dp_secondary_date_of_birth = fields.Date(string="Secondary Date of Birth")
    dp_secondary_email = fields.Char(string="Secondary Email")

    # Referral / Login
    dp_referral_code = fields.Char(string="Referral Code")
    dp_new_username = fields.Char(string="New Username")
    dp_new_password = fields.Char(string="New Password")

    # Customer Identity
    dp_customer_dlicense = fields.Char(string="Driver License")
    dp_customer_dlicense_state = fields.Char(string="DL State")
    dp_customer_dlicense_exp = fields.Date(string="DL Expiry")
    dp_customer_passport = fields.Char(string="Passport")
    dp_customer_passport_exp = fields.Date(string="Passport Expiry")
    dp_customer_medicare = fields.Char(string="Medicare")
    dp_customer_medicare_ref = fields.Char(string="Medicare Ref")

    # Employment
    dp_position_at_current_employer = fields.Char(string="Position at Current Employer")
    dp_employment_status = fields.Char(string="Employment Status")
    dp_current_employer = fields.Char(string="Current Employer")
    dp_employer_contact_number = fields.Char(string="Employer Contact Number")
    dp_years_in_employment = fields.Integer(string="Years in Employment")
    dp_months_in_employment = fields.Integer(string="Months in Employment")
    dp_employment_confirmation = fields.Boolean(string="Employment Confirmation")

    # Life Support
    dp_life_support = fields.Boolean(string="Life Support", default=False)
    dp_life_support_machine_type = fields.Char(string="Life Support Machine Type")
    dp_life_support_details = fields.Text(string="Life Support Details")

    # Energy Identifiers
    dp_nmi = fields.Char(string="NMI")
    dp_nmi_source = fields.Char(string="NMI Source")
    dp_mirn = fields.Char(string="MIRN")
    dp_mirn_source = fields.Char(string="MIRN Source")

    # Connection Info
    dp_connection_date = fields.Date(string="Connection Date")
    dp_electricity_connection = fields.Boolean(string="Electricity Connection")
    dp_gas_connection = fields.Boolean(string="Gas Connection")
    dp_12_month_disconnection = fields.Boolean(string="12 Month Disconnection")

    # Certificates
    dp_cert_electrical_safety = fields.Boolean(string="Electrical Safety Cert")
    dp_cert_electrical_safety_id = fields.Char(string="Cert Electrical Safety ID")
    dp_cert_electrical_safety_sent = fields.Boolean(string="Cert Sent")

    # Consent
    dp_explicit_informed_consent = fields.Boolean(string="Explicit Informed Consent")

    # Compliance / Audit
    dp_center_name = fields.Char(string="Center Name")
    dp_closer_name = fields.Char(string="Closer Name")
    dp_dnc_wash_number = fields.Char(string="DNC Wash Number")
    dp_dnc_exp_date = fields.Date(string="DNC Exp Date")
    dp_audit_1 = fields.Char(string="Audit-1")
    dp_audit_2 = fields.Char(string="Audit-2")
    dp_welcome_call = fields.Boolean(string="Welcome Call")  



    @api.model
    def _save_dodo_power_data(self):
        """
        Save Dodo Power form data per stage in custom.dodo.power.form
        """
        for lead in self:
            stage = lead.dodo_power_stage
            if not stage:
                continue

            DodoPowerForm = self.env['custom.dodo.power.form']

            # Check if record for this lead and stage exists
            existing = DodoPowerForm.search([
                ('lead_id', '=', lead.id),
                ('stage', '=', stage)
            ], limit=1)

            dp_vals = {
                # Base
                'lead_id': lead.id,
                'stage': stage,

                # Compliance / Internal
                'internal_dnc_checked': lead.dp_internal_dnc_checked,
                'existing_sale': lead.dp_existing_sale,
                'online_enquiry_form': lead.dp_online_enquiry_form,

                # Sales Info
                'sales_name': lead.dp_sales_name,
                'sales_reference': lead.dp_sales_reference,
                'agreement_date': lead.dp_agreement_date,

                # Site / Address
                'site_address_postcode': lead.dp_site_address_postcode,
                'site_addr_unit_type': lead.dp_site_addr_unit_type,
                'site_addr_unit_no': lead.dp_site_addr_unit_no,
                'site_addr_floor_type': lead.dp_site_addr_floor_type,
                'site_addr_floor_no': lead.dp_site_addr_floor_no,
                'site_addr_street_no': lead.dp_site_addr_street_no,
                'site_addr_street_no_suffix': lead.dp_site_addr_street_no_suffix,
                'site_addr_street_name': lead.dp_site_addr_street_name,
                'site_addr_street_type': lead.dp_site_addr_street_type,
                'site_addr_suburb': lead.dp_site_addr_suburb,
                'site_addr_state': lead.dp_site_addr_state,
                'site_addr_postcode': lead.dp_site_addr_postcode,
                'site_addr_desc': lead.dp_site_addr_desc,
                'site_access': lead.dp_site_access,
                'site_more_than_12_months': lead.dp_site_more_than_12_months,

                # Previous Address
                'prev_addr_1': lead.dp_prev_addr_1,
                'prev_addr_2': lead.dp_prev_addr_2,
                'prev_addr_state': lead.dp_prev_addr_state,
                'prev_addr_postcode': lead.dp_prev_addr_postcode,

                # Billing Address
                'billing_address': lead.dp_billing_address,
                'bill_addr_1': lead.dp_bill_addr_1,
                'bill_addr_2': lead.dp_bill_addr_2,
                'bill_addr_state': lead.dp_bill_addr_state,
                'bill_addr_postcode': lead.dp_bill_addr_postcode,

                # Concessions
                'concession': lead.dp_concession,
                'concession_card_type': lead.dp_concession_card_type,
                'concession_card_no': lead.dp_concession_card_no,
                'concession_start_date': lead.dp_concession_start_date,
                'concession_exp_date': lead.dp_concession_exp_date,
                'concession_first_name': lead.dp_concession_first_name,
                'concession_middle_name': lead.dp_concession_middle_name,
                'concession_last_name': lead.dp_concession_last_name,

                # Product / Energy
                'product_code': lead.dp_product_code,
                'meter_type': lead.dp_meter_type,
                'kwh_usage_per_day': lead.dp_kwh_usage_per_day,
                'how_many_people': lead.dp_how_many_people,
                'how_many_bedrooms': lead.dp_how_many_bedrooms,
                'solar_power': lead.dp_solar_power,
                'solar_type': lead.dp_solar_type,
                'solar_output': lead.dp_solar_output,
                'green_energy': lead.dp_green_energy,
                'winter_gas_usage': lead.dp_winter_gas_usage,
                'summer_gas_usage': lead.dp_summer_gas_usage,
                'monthly_winter_spend': lead.dp_monthly_winter_spend,
                'monthly_summer_spend': lead.dp_monthly_summer_spend,

                # Invoice
                'invoice_method': lead.dp_invoice_method,

                # Customer Info
                'customer_salutation': lead.dp_customer_salutation,
                'first_name': lead.dp_first_name,
                'last_name': lead.dp_last_name,
                'date_of_birth': lead.dp_date_of_birth,
                'email_contact': lead.dp_email_contact,
                'contact_number': lead.dp_contact_number,
                'hearing_impaired': lead.dp_hearing_impaired,

                # Secondary Contact
                'secondary_contact': lead.dp_secondary_contact,
                'secondary_salutation': lead.dp_secondary_salutation,
                'secondary_first_name': lead.dp_secondary_first_name,
                'secondary_last_name': lead.dp_secondary_last_name,
                'secondary_date_of_birth': lead.dp_secondary_date_of_birth,
                'secondary_email': lead.dp_secondary_email,

                # Referral / Login
                'referral_code': lead.dp_referral_code,
                'new_username': lead.dp_new_username,
                'new_password': lead.dp_new_password,

                # Customer Identity
                'customer_dlicense': lead.dp_customer_dlicense,
                'customer_dlicense_state': lead.dp_customer_dlicense_state,
                'customer_dlicense_exp': lead.dp_customer_dlicense_exp,
                'customer_passport': lead.dp_customer_passport,
                'customer_passport_exp': lead.dp_customer_passport_exp,
                'customer_medicare': lead.dp_customer_medicare,
                'customer_medicare_ref': lead.dp_customer_medicare_ref,

                # Employment
                'position_at_current_employer': lead.dp_position_at_current_employer,
                'employment_status': lead.dp_employment_status,
                'current_employer': lead.dp_current_employer,
                'employer_contact_number': lead.dp_employer_contact_number,
                'years_in_employment': lead.dp_years_in_employment,
                'months_in_employment': lead.dp_months_in_employment,
                'employment_confirmation': lead.dp_employment_confirmation,

                # Life Support
                'life_support': lead.dp_life_support,
                'life_support_machine_type': lead.dp_life_support_machine_type,
                'life_support_details': lead.dp_life_support_details,

                # Energy Identifiers
                'nmi': lead.dp_nmi,
                'nmi_source': lead.dp_nmi_source,
                'mirn': lead.dp_mirn,
                'mirn_source': lead.dp_mirn_source,

                # Connection Info
                'connection_date': lead.dp_connection_date,
                'electricity_connection': lead.dp_electricity_connection,
                'gas_connection': lead.dp_gas_connection,
                'twelve_month_disconnection': lead.dp_12_month_disconnection,

                # Certificates
                'cert_electrical_safety': lead.dp_cert_electrical_safety,
                'cert_electrical_safety_id': lead.dp_cert_electrical_safety_id,
                'cert_electrical_safety_sent': lead.dp_cert_electrical_safety_sent,

                # Consent
                'explicit_informed_consent': lead.dp_explicit_informed_consent,

                # Compliance / Audit
                'center_name': lead.dp_center_name,
                'closer_name': lead.dp_closer_name,
                'dnc_wash_number': lead.dp_dnc_wash_number,
                'dnc_exp_date': lead.dp_dnc_exp_date,
                'audit_1': lead.dp_audit_1,
                'audit_2': lead.dp_audit_2,
                'welcome_call': lead.dp_welcome_call,
            }

            if existing:
                existing.write(dp_vals)
            else:
                DodoPowerForm.create(dp_vals) 

    @api.onchange('dodo_power_stage')
    def _onchange_dodo_power_stage(self):
        """
        Load Dodo Power form data from saved stage when user changes stage
        """
        for rec in self:
            if not rec.dodo_power_stage:
                return

            DodoPowerForm = self.env['custom.dodo.power.form']
            existing = DodoPowerForm.search([
                ('lead_id', '=', rec._origin.id),
                ('stage', '=', rec.dodo_power_stage)
            ], limit=1)

            if existing:
                # Compliance / Internal
                rec.dp_internal_dnc_checked = existing.internal_dnc_checked
                rec.dp_existing_sale = existing.existing_sale
                rec.dp_online_enquiry_form = existing.online_enquiry_form

                # Sales Info
                rec.dp_sales_name = existing.sales_name
                rec.dp_sales_reference = existing.sales_reference
                rec.dp_agreement_date = existing.agreement_date

                # Site / Address
                rec.dp_site_address_postcode = existing.site_address_postcode
                rec.dp_site_addr_unit_type = existing.site_addr_unit_type
                rec.dp_site_addr_unit_no = existing.site_addr_unit_no
                rec.dp_site_addr_floor_type = existing.site_addr_floor_type
                rec.dp_site_addr_floor_no = existing.site_addr_floor_no
                rec.dp_site_addr_street_no = existing.site_addr_street_no
                rec.dp_site_addr_street_no_suffix = existing.site_addr_street_no_suffix
                rec.dp_site_addr_street_name = existing.site_addr_street_name
                rec.dp_site_addr_street_type = existing.site_addr_street_type
                rec.dp_site_addr_suburb = existing.site_addr_suburb
                rec.dp_site_addr_state = existing.site_addr_state
                rec.dp_site_addr_postcode = existing.site_addr_postcode
                rec.dp_site_addr_desc = existing.site_addr_desc
                rec.dp_site_access = existing.site_access
                rec.dp_site_more_than_12_months = existing.site_more_than_12_months

                # Previous Address
                rec.dp_prev_addr_1 = existing.prev_addr_1
                rec.dp_prev_addr_2 = existing.prev_addr_2
                rec.dp_prev_addr_state = existing.prev_addr_state
                rec.dp_prev_addr_postcode = existing.prev_addr_postcode

                # Billing Address
                rec.dp_billing_address = existing.billing_address
                rec.dp_bill_addr_1 = existing.bill_addr_1
                rec.dp_bill_addr_2 = existing.bill_addr_2
                rec.dp_bill_addr_state = existing.bill_addr_state
                rec.dp_bill_addr_postcode = existing.bill_addr_postcode

                # Concessions
                rec.dp_concession = existing.concession
                rec.dp_concession_card_type = existing.concession_card_type
                rec.dp_concession_card_no = existing.concession_card_no
                rec.dp_concession_start_date = existing.concession_start_date
                rec.dp_concession_exp_date = existing.concession_exp_date
                rec.dp_concession_first_name = existing.concession_first_name
                rec.dp_concession_middle_name = existing.concession_middle_name
                rec.dp_concession_last_name = existing.concession_last_name

                # Product / Energy Details
                rec.dp_product_code = existing.product_code
                rec.dp_meter_type = existing.meter_type
                rec.dp_kwh_usage_per_day = existing.kwh_usage_per_day
                rec.dp_how_many_people = existing.how_many_people
                rec.dp_how_many_bedrooms = existing.how_many_bedrooms
                rec.dp_solar_power = existing.solar_power
                rec.dp_solar_type = existing.solar_type
                rec.dp_solar_output = existing.solar_output
                rec.dp_green_energy = existing.green_energy
                rec.dp_winter_gas_usage = existing.winter_gas_usage
                rec.dp_summer_gas_usage = existing.summer_gas_usage
                rec.dp_monthly_winter_spend = existing.monthly_winter_spend
                rec.dp_monthly_summer_spend = existing.monthly_summer_spend

                # Invoice
                rec.dp_invoice_method = existing.invoice_method

                # Customer Info
                rec.dp_customer_salutation = existing.customer_salutation
                rec.dp_first_name = existing.first_name
                rec.dp_last_name = existing.last_name
                rec.dp_date_of_birth = existing.date_of_birth
                rec.dp_email_contact = existing.email_contact
                rec.dp_contact_number = existing.contact_number
                rec.dp_hearing_impaired = existing.hearing_impaired

                # Secondary Contact
                rec.dp_secondary_contact = existing.secondary_contact
                rec.dp_secondary_salutation = existing.secondary_salutation
                rec.dp_secondary_first_name = existing.secondary_first_name
                rec.dp_secondary_last_name = existing.secondary_last_name
                rec.dp_secondary_date_of_birth = existing.secondary_date_of_birth
                rec.dp_secondary_email = existing.secondary_email

                # Referral / Login
                rec.dp_referral_code = existing.referral_code
                rec.dp_new_username = existing.new_username
                rec.dp_new_password = existing.new_password

                # Customer Identity
                rec.dp_customer_dlicense = existing.customer_dlicense
                rec.dp_customer_dlicense_state = existing.customer_dlicense_state
                rec.dp_customer_dlicense_exp = existing.customer_dlicense_exp
                rec.dp_customer_passport = existing.customer_passport
                rec.dp_customer_passport_exp = existing.customer_passport_exp
                rec.dp_customer_medicare = existing.customer_medicare
                rec.dp_customer_medicare_ref = existing.customer_medicare_ref

                # Employment
                rec.dp_position_at_current_employer = existing.position_at_current_employer
                rec.dp_employment_status = existing.employment_status
                rec.dp_current_employer = existing.current_employer
                rec.dp_employer_contact_number = existing.employer_contact_number
                rec.dp_years_in_employment = existing.years_in_employment
                rec.dp_months_in_employment = existing.months_in_employment
                rec.dp_employment_confirmation = existing.employment_confirmation

                # Life Support
                rec.dp_life_support = existing.life_support
                rec.dp_life_support_machine_type = existing.life_support_machine_type
                rec.dp_life_support_details = existing.life_support_details

                # Energy Identifiers
                rec.dp_nmi = existing.nmi
                rec.dp_nmi_source = existing.nmi_source
                rec.dp_mirn = existing.mirn
                rec.dp_mirn_source = existing.mirn_source

                # Connection Info
                rec.dp_connection_date = existing.connection_date
                rec.dp_electricity_connection = existing.electricity_connection
                rec.dp_gas_connection = existing.gas_connection
                rec.dp_12_month_disconnection = existing.twelve_month_disconnection

                # Certificates
                rec.dp_cert_electrical_safety = existing.cert_electrical_safety
                rec.dp_cert_electrical_safety_id = existing.cert_electrical_safety_id
                rec.dp_cert_electrical_safety_sent = existing.cert_electrical_safety_sent

                # Consent
                rec.dp_explicit_informed_consent = existing.explicit_informed_consent

                # Compliance / Audit
                rec.dp_center_name = existing.center_name
                rec.dp_closer_name = existing.closer_name
                rec.dp_dnc_wash_number = existing.dnc_wash_number
                rec.dp_dnc_exp_date = existing.dnc_exp_date
                rec.dp_audit_1 = existing.audit_1
                rec.dp_audit_2 = existing.audit_2
                rec.dp_welcome_call = existing.welcome_call

            else:
                # Reset all fields to defaults if no existing data found
                rec.update({fname: False for fname in self._fields if fname.startswith("dp_")})
                      

                          
           


   
