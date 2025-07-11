from odoo import models, fields

class CustomEnergyCompareForm(models.Model):
    _name = 'custom.energy.compare.form'
    _description = 'Energy Compare Form'

    lead_id = fields.Many2one('crm.lead', string="Lead")
    stage = fields.Selection([
        ('1', 'Stage 1'), ('2', 'Stage 2'), ('3', 'Stage 3'), ('4', 'Stage 4'), ('5', 'Stage 5')
    ], string="Stage")

    current_address = fields.Char(string="Current Address")
    what_to_compare = fields.Selection([
        ('electricity_gas', 'Electricity & Gas'),
        ('electricity', 'Elecricity'),
    ], string="What are you looking to compare?")
    property_type = fields.Selection([
        ('residential', 'Residential'),
        ('business', 'Business'),
    ], string="What type of property?")
    moving_in = fields.Boolean(string="Are you moving into this property?")
    date = fields.Date("date")
    property_ownership = fields.Selection([
        ('own', 'Own'),
        ('rent', 'Rent'),
    ], string="Do you own or rent this property?")
    usage_profile = fields.Selection([
        ('low', '1-2 people, spemd minimal time at home, weekly washing, minimal heating, cooking.'),
        ('medium', '3-4 people, home in the evening and weekend regular washing, heating and cooling.'),
        ('high', '5+ people, home during the day, evenings and weekend daily washing, heating and cooling.')
    ], string="Usage Profile")
    require_life_support = fields.Boolean(string="Does anyone residing or intending to reside at your premises require life support equipment?")
    concesion_card_holder = fields.Boolean("Are you a concession card holder?")
    rooftop_solar = fields.Boolean(string="Do you have rooftop solar panels")
    electricity_provider = fields.Selection([
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

    gas_provider = fields.Selection([
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
    name = fields.Char("name")
    contact_number = fields.Char("contact_number")
    email = fields.Char("email")
    request_callback = fields.Boolean(string="Request a call back")
    accpeting_terms = fields.Boolean(string="By submitting your details you agree that you have read and agreed to the Terms and Conditions and Privacy Policy.")