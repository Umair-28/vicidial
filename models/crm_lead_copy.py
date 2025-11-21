import re
from odoo import models, fields, api, _
from datetime import timezone, date
import logging
import json
import requests
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from lxml import etree
import base64
import io
import xlsxwriter
from datetime import datetime
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    external_api_id = fields.Integer("External API ID", index=True)
    vicidial_lead_id = fields.Integer("Vicidial Lead Id")
    partner_latitude = fields.Float(
        string="Latitude", related="partner_id.partner_latitude", store=True
    )

    partner_longitude = fields.Float(
        string="Longitude", related="partner_id.partner_longitude", store=True
    )

    # Example: Custom field for automatic assignment logic
    assignation_id = fields.Many2one(
        "res.partner", string="Automatically Assigned Partner"
    )

    unlock_stage_1 = fields.Boolean(default=False)
    unlock_stage_2 = fields.Boolean(default=False)
    unlock_stage_3 = fields.Boolean(default=False)
    unlock_stage_4 = fields.Boolean(default=False)

    unlock_previous_stage = fields.Boolean(
            string="Unlock Previous Stage",
            default=True,
            help="Allows editing of previous stage fields.",
            store=True
        )

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """Lock all stages again when moving forward"""
        for rec in self:
            rec.unlock_stage_1 = False
            rec.unlock_stage_2 = False
            rec.unlock_stage_3 = False
            rec.unlock_stage_4 = False


    def action_toggle_stage_lock(self):
        stage_number = self.env.context.get("stage_number")
        unlock = self.env.context.get("unlock")

        if stage_number and unlock is not None:
            field_name = f"unlock_stage_{stage_number}"
            self.write({field_name: unlock})

        # Return custom action that will scroll after reload
        return {
            "type": "ir.actions.client",
            "tag": "scroll_and_reload",
            "params": {
                "stage_number": stage_number,
                "unlock": unlock,  # Pass unlock parameter
            }
        }




    services = fields.Selection(
        [
            ("credit_card_call_center", "Credit Card (Call Center)"),
            ("credit_card_website", "Credit Card (Website)"),
            ("energy_call_center", "Electricity & Gas (Call Center)"),
            ("energy_website", "Electricity & Gas (Webite)"),
            ("optus_nbn_call_center", "Broadband (Call Center)"),
            ("optus_nbn_website", "Broadband (Website)"),
            ("home_moving", "Home Moving"),
            ("business_loan", "Business Loan"),
            ("home_loan", "Home Loan"),
            ("insurance", "Health Insurance"),
            ("veu", "Victorian Energy"),
        ],
        required=True,
    )

    @api.constrains(
        "momentum_energy_transaction_reference",
        "momentum_energy_transaction_channel",
        "momentum_energy_transaction_verification_code",
        "momentum_energy_transaction_source",
        "momentum_energy_passport_id",
        "momentum_energy_driving_license_id",
        "momentum_energy_medicare_id",
        "momentum_energy_medicare_number",
        "momentum_energy_entity_name",
        "momentum_energy_trading_name",
        "momentum_energy_trustee_name",
        "momentum_energy_abn_document_id",
        "momentum_energy_acn_document_id",
        "momentum_energy_primary_contact_type",
        "momentum_energy_primary_first_name",
        "momentum_energy_primary_last_name",
        # "momentum_energy_primary_email",
        "momentum_energy_primary_street_number",
        "momentum_energy_primary_street_name",
        "momentum_energy_primary_unit_number",
        "momentum_energy_primary_suburb",
        "momentum_energy_primary_post_code",
        "momentum_energy_primary_phone_work",
        "momentum_energy_primary_phone_home",
        "momentum_energy_primary_phone_mobile",
        "momentum_energy_secondary_contact_type",
        "momentum_energy_secondary_first_name",
        "momentum_energy_secondary_last_name",
        "momentum_energy_secondary_country_of_birth",
        "momentum_energy_secondary_email",
        "momentum_energy_secondary_phone_work",
        "momentum_energy_secondary_phone_home",
        "momentum_energy_secondary_phone_mobile",
        "momentum_energy_secondary_unit_number",
        "momentum_energy_secondary_street_number",
        "momentum_energy_secondary_street_name",
        "momentum_energy_secondary_post_code",
        "momentum_energy_service_connection_id",
        "momentum_energy_service_street_number",
        "momentum_energy_estimated_annual_kwhs",
        "momentum_energy_service_street_name",
        "momentum_energy_service_suburb",
        "momentum_energy_service_post_code",
        "momentum_energy_service_offer_code",
        "momentum_energy_floor_number",
        "momentum_energy_conc_card_code",
        "momentum_energy_conc_card_number",
        "momentum_energy_card_first_name",
        "momentum_energy_card_last_name",
        "momentum_energy_secondary_email",
    )
    def _check_field_validations(self):
        """
        Unified field validation for all Momentum Energy fields.
        """
        # Predefined regex patterns for different field types
        patterns = {
            "momentum_energy_transaction_reference": (
                r"^[A-Za-z0-9\-]{1,30}$",
                "Invalid Transaction Reference. Use only letters, digits, and hyphens (-), max 30 chars.",
            ),
            "momentum_energy_transaction_channel": (
                r"^[A-Za-z0-9\s]+$",
                "Invalid Transaction Channel. Only letters, numbers, and spaces are allowed.",
            ),
            "momentum_energy_transaction_verification_code": (
                r"^[A-Za-z0-9\-]{1,30}$",
                "Invalid Transaction Verification Code. Use only letters, digits, and hyphens (-), max 30 chars.",
            ),
            "momentum_energy_transaction_source": (
                r"^[A-Za-z\s]+$",
                "Invalid Transaction Source. Only letters and spaces are allowed.",
            ),
            "momentum_energy_passport_id": (
                r"^[A-Za-z0-9\-]{1,30}$",
                "Invalid Passport Number. Use only letters, digits, and hyphens (-), max 30 chars.",
            ),
            "momentum_energy_driving_license_id": (
                r"^[A-Za-z0-9\-]{1,30}$",
                "Invalid Driving Liscense Number. Use only letters, digits, and hyphens (-), max 30 chars.",
            ),
            "momentum_energy_medicare_id": (
                r"^[A-Za-z0-9\-]{1,30}$",
                "Invalid Medicare Number. Use only letters, digits, and hyphens (-), max 30 chars.",
            ),
            "momentum_energy_medicare_number": (
                r"^[0-9]{1,30}$",
                "Invalid Medicare Document Number. Only digits (0–9) are allowed, with a maximum length of 30 characters",
            ),
            "momentum_energy_entity_name": (
                r"^[A-Za-z0-9][A-Za-z0-9'&@/()., -]{1,100}$",
                "Invalid Entity Name. It must start with a letter or number and can include letters, numbers, spaces, and special characters (' & @ / ( ) . , -). Maximum length: 100 characters.",
            ),
            "momentum_energy_trading_name": (
                r"^[A-Za-z0-9][A-Za-z0-9'&@/()., -]{1,100}$",
                "Invalid Trading Name. It must start with a letter or number and can include letters, numbers, spaces, and special characters (' & @ / ( ) . , -). Maximum length: 100 characters.",
            ),
            "momentum_energy_trustee_name": (
                r"^[A-Za-z0-9][A-Za-z0-9'&@/()., -]{1,100}$",
                "Invalid Trustee Name. It must start with a letter or number and can include letters, numbers, spaces, and special characters (' & @ / ( ) . , -). Maximum length: 100 characters.",
            ),
            "momentum_energy_abn_document_id": (
                r"^\d{11}$",
                "Invalid ABN Number. It must contain exactly 11 digits with no spaces or special characters.",
            ),
            "momentum_energy_acn_document_id": (
                r"^\d{9}$",
                "Invalid ACN Number. It must contain exactly 9 digits with no spaces or special characters.",
            ),
            "momentum_energy_primary_contact_type": (
                r"^[A-Za-z\s]+$",
                "Invalid Primary Contact Type. Only letters are allowed.",
            ),
            "momentum_energy_primary_first_name": (
                r"^[A-Z][a-zA-Z'-. ]{1,100}$",
                "Invalid Customer First Name. It must start with a capital letter and can contain only letters, apostrophes ('), hyphens (-), periods (.), and spaces. Maximum length is 100 characters.",
            ),
            "momentum_energy_primary_last_name": (
                r"^[A-Z][a-zA-Z'-. ]{1,100}$",
                "Invalid Customer Last Name. It must start with a capital letter and can contain only letters, apostrophes ('), hyphens (-), periods (.), and spaces. Maximum length is 100 characters.",
            ),
            # "momentum_energy_primary_email": (
            #     r"^[a-zA-Z0-9._|%#~`=?&/$^*!}{+\-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$",
            #     "Invalid Email Address. It must follow the format 'example@domain.com' and can include letters, numbers, and special characters (._|%#~`=?&/$^*!}{+-) before the '@'.",
            # ),
            "momentum_energy_primary_street_number": (
                r"^[A-Za-z0-9-]*$",
                "Invalid Street Number. Only letters (A–Z, a–z), numbers (0–9), and hyphens (-) are allowed.",
            ),
            "momentum_energy_primary_street_name": (
                r"^[a-zA-Z0-9'.,/()\-\s]+$",
                "Invalid Street Name. Only letters (A–Z, a–z), numbers (0–9), spaces, and special characters (', . / ( ) -) are allowed.",
            ),
            "momentum_energy_primary_unit_number": (
                r"^[a-zA-Z0-9'.,/()\-\s]+$",
                "Invalid Primary Unit Number. Only letters (A–Z, a–z), numbers (0–9), spaces, and the special characters (', . / ( ) -) are allowed.",
            ),
            "momentum_energy_primary_suburb": (
                r"^[A-Za-z0-9-]*$",
                "Invalid Suburb. Only letters (A–Z, a–z), numbers (0–9), and hyphens (-) are allowed.",
            ),
            "momentum_energy_primary_post_code": (
                r"^[0-9]{4}$",
                "Invalid Primary PIN Code format. It must contain exactly 4 digits (0–9).",
            ),
            "momentum_energy_primary_phone_work": (
                r"^(0[2378]\d{8}|0\d{9}|13\d{4}|1300\d{6}|1800\d{6})$",
                "Invalid Primary Phone Work Number format. Must be a valid Australian phone number such as landline, mobile, or toll-free (13, 1300, 1800).",
            ),
            "momentum_energy_primary_phone_home": (
                r"^(0[2378]\d{8}|0\d{9}|13\d{4}|1300\d{6}|1800\d{6})$",
                "Invalid Primary Phone Home Number format. Must be a valid Australian phone number such as landline, mobile, or toll-free (13, 1300, 1800).",
            ),
            "momentum_energy_primary_phone_mobile": (
                r"^(0[2378]\d{8}|0\d{9}|13\d{4}|1300\d{6}|1800\d{6})$",
                "Invalid Primary Phone Mobile Number format. Must be a valid Australian phone number such as landline, mobile, or toll-free (13, 1300, 1800).",
            ),
            "momentum_energy_secondary_contact_type": (
                r"^[A-Za-z\s]+$",
                "Invalid Secondary Contact Type. Only letters are allowed.",
            ),
            "momentum_energy_secondary_first_name": (
                r"^[A-Z][a-zA-Z'-. ]{1,100}$",
                "Invalid Customer Secondary First Name. It must start with a capital letter and can contain only letters, apostrophes ('), hyphens (-), periods (.), and spaces. Maximum length is 100 characters.",
            ),
            "momentum_energy_secondary_last_name": (
                r"^[A-Z][a-zA-Z'-. ]{1,100}$",
                "Invalid Customer Secondary Last Name. It must start with a capital letter and can contain only letters, apostrophes ('), hyphens (-), periods (.), and spaces. Maximum length is 100 characters.",
            ),
            "momentum_energy_secondary_country_of_birth": (
                r"^[A-Za-z]+$",
                "Invalid Customer Secondary Country of Birth. Only letters are allowed.",
            ),
            "momentum_energy_secondary_email": (
                r"^[a-zA-Z0-9._|%#~`=?&/$^*!}{+\-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$",
                "Invalid Email Address. It must follow the format 'example@domain.com' and can include letters, numbers, and special characters (._|%#~`=?&/$^*!}{+-) before the '@'.",
            ),
            "momentum_energy_secondary_phone_work": (
                r"^(0[2378]\d{8}|0\d{9}|13\d{4}|1300\d{6}|1800\d{6})$",
                "Invalid Secondary Phone Work Number format. Must be a valid Australian phone number such as landline, mobile, or toll-free (13, 1300, 1800).",
            ),
            "momentum_energy_secondary_phone_home": (
                r"^(0[2378]\d{8}|0\d{9}|13\d{4}|1300\d{6}|1800\d{6})$",
                "Invalid Secondary Phone Home Number format. Must be a valid Australian phone number such as landline, mobile, or toll-free (13, 1300, 1800).",
            ),
            "momentum_energy_secondary_phone_mobile": (
                r"^(0[2378]\d{8}|0\d{9}|13\d{4}|1300\d{6}|1800\d{6})$",
                "Invalid Secondary Phone Mobile Number format. Must be a valid Australian phone number such as landline, mobile, or toll-free (13, 1300, 1800).",
            ),
            "momentum_energy_secondary_unit_number": (
                r"^[0-9]+$",
                "Invalid Secondary Unit Number. Only digits (0–9) are allowed.",
            ),
            "momentum_energy_secondary_street_number": (
                r"^[A-Za-z0-9-]*$",
                "Invalid Secondary Street Number. Only letters (A–Z, a–z), numbers (0–9), and hyphens (-) are allowed.",
            ),
            "momentum_energy_secondary_street_name": (
                r"^[A-Za-z\s]+$",
                "Invalid Secondary Street Name. Only letters and spaces are allowed.",
            ),
            "momentum_energy_secondary_post_code": (
                r"^[0-9]+$",
                "Invalid Secondary Post Code. Only digits (0–9) are allowed.",
            ),
            "momentum_energy_service_connection_id": (
                r"^[0-9A-Za-z]+$",
                "Invalid Service Connection ID input. Only letters (A–Z, a–z) and numbers (0–9) are allowed, with no spaces or special characters.",
            ),
            "momentum_energy_service_street_number": (
                r"^[A-Za-z0-9-]*$",
                "Invalid Service Street Number. Only letters (A–Z, a–z), numbers (0–9), and hyphens (-) are allowed.",
            ),
            "momentum_energy_service_street_name": (
                r"^[a-zA-Z0-9'.,/()\-\s]+$",
                "Invalid Service Street Name. Only letters (A–Z, a–z), numbers (0–9), spaces, and the special characters (', . / ( ) -) are allowed.",
            ),
            "momentum_energy_service_suburb": (
                r"^[A-Za-z0-9 ]*$",
                "Invalid Service Suburb input. Only letters (A–Z, a–z), numbers (0–9), and spaces are allowed. Special characters are not permitted.",
            ),
            "momentum_energy_estimated_annual_kwhs": (
                r"^[0-9]+$",
                "Invalid Estimated Annual KWHS. Only digits (0–9) are allowed.",
            ),
            "momentum_energy_service_post_code": (
                r"^[0-9]{4}$",
                "Invalid Service PIN Code format. It must contain exactly 4 digits (0–9).",
            ),
            "momentum_energy_service_offer_code": (
                r"^[a-zA-Z0-9]{15}(?:[a-zA-Z0-9]{3})?$",
                "Invalid Service Offer Code input. Must be 15 or 18 alphanumeric characters (letters and numbers only, no spaces or symbols).",
            ),
            "momentum_energy_floor_number": (
                r"^[0-9]+$",
                "Invalid Floor Number. Only digits (0–9) are allowed.",
            ),
            "momentum_energy_conc_card_code": (
                r"^[A-Za-z0-9\-]+$",
                "Invalid Concession Card Code input. Only letters, numbers, and hyphens (-) are allowed. No spaces or special characters.",
            ),
            "momentum_energy_conc_card_number": (
                r"^[A-Za-z0-9\-]{1,30}$",
                "Invalid Concession Card Number. Use only letters, digits, and hyphens (-), max 30 chars.",
            ),
            "momentum_energy_card_first_name": (
                r"^[A-Z][a-zA-Z'-. ]{1,100}$",
                "Invalid Concession Card Holder First Name. It must start with a capital letter and can contain only letters, apostrophes ('), hyphens (-), periods (.), and spaces. Maximum length is 100 characters.",
            ),
            "momentum_energy_card_last_name": (
                r"^[A-Z][a-zA-Z'-. ]{1,100}$",
                "Invalid Concession Card Holder Last Name. It must start with a capital letter and can contain only letters, apostrophes ('), hyphens (-), periods (.), and spaces. Maximum length is 100 characters.",
            ),
            "momentum_energy_secondary_email": (
                r"^[a-zA-Z0-9._|%#~`=?&/$^*!}{+\-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$",
                "Invalid Secondary Email Address. It must follow the format 'example@domain.com' and can include letters, numbers, and special characters (._|%#~`=?&/$^*!}{+-) before the '@'.",
            ),
        }
        required_fields = {
            "momentum_energy_transaction_reference": "Sale Reference Number is required.",
            "momentum_energy_transaction_channel":"Transactional Channel name is required",
            "momentum_energy_transaction_date":"Transaction Date is required",
            "momentum_energy_customer_type":"Customer Type is required",
            "momentum_energy_primary_first_name": "Primary First Name is required.",
            "momentum_energy_primary_last_name": "Primary Last Name is required.",
            "momentum_energy_primary_phone_home":"Home phone number is required",
            "momentum_energy_primary_unit_number":"Primary Contact Address Unit Number is required",
            "momentum_energy_primary_street_number":"Primary Contact Address Street Number is required",
            "momentum_energy_primary_street_name":"Primary Contact Address Street Name is required",
            "momentum_energy_primary_suburb":"Primary Contact Address Suburb is required",
            "momentum_energy_primary_state":"Primary Contact Address State is required",
            "momentum_energy_primary_post_code":"Primary Contact Address Post Code is required",
            "momentum_energy_service_type":"Service Type is required",
            "momentum_energy_service_sub_type":"Service Sub Type is required",
            "momentum_energy_service_connection_id":"Service Connection ID is required, NMI / MIRN of the site, depending on the type of the service if service is POWER, it must be NMI and MIRN for GAS",
            "momentum_energy_estimated_annual_kwhs":"Site's estimated annual consumption is required",
            "momentum_energy_service_street_number":"Service Address Street Number is required",
            "momentum_energy_service_street_name":"Service Street Address Name is required",
            "momentum_energy_service_street_type_code":"Service Address Street Code Type is required",
            "momentum_energy_service_suburb":"Service Address Suburb is required",
            "momentum_energy_service_state":"Service Address State is required",
            "momentum_energy_service_post_code":"Service Address Post Code is required",
            "momentum_energy_offer_quote_date":"Offer Quote Date is required",
            "momentum_energy_service_offer_code":"Service Offer Code is required",
            "momentum_energy_service_plan_code":"Service Plan Code is required",
            "momentum_energy_contract_term_code":"Contract Term Code is required",
            "momentum_energy_contract_date":"Contract Date is required",
            "momentum_energy_payment_method":"Payment Method is required",
            "momentum_energy_bill_cycle_code":"Bill Cycle Code is required",
            "momentum_energy_bill_delivery_method":"Bill Delivery Method is required",


        }

        for rec in self:
            # ✅ Run validation only when lead is in Stage 4
            if str(rec.lead_stage) == "4" and (rec.stage_2_campign_name or "").lower() == "momentum":
                _logger.info("************************************")
                for field, (pattern, msg) in patterns.items():
                    if hasattr(rec, field):
                        value = getattr(rec, field)

                        # 🔒 Check required fields
                        if field in required_fields and not value:
                            raise ValidationError(_(required_fields[field]))

                        # 🔍 Validate pattern if value exists
                        if value:
                            if not isinstance(value, str):
                                value = str(value)
                            value = value.strip()

                            if not re.fullmatch(pattern, value):
                                raise ValidationError(_(msg))


    @api.constrains("momentum_energy_customer_type", "momentum_energy_customer_sub_type")
    def _check_customer_sub_type(self):
        for rec in self:
            # ✅ Validate only on Stage 4 and Momentum campaign
            if (
                (str(rec.lead_stage) == "4" or getattr(rec.lead_stage, "id", None) == 4)
                and (rec.stage_2_campign_name or "").lower() == "momentum"
            ):
                # 🏠 Rule for Resident customers
                if rec.momentum_energy_customer_type == "RESIDENT":
                    if rec.momentum_energy_customer_sub_type != "RESIDENT":
                        raise ValidationError(
                            _("For a Resident customer, the Sub Type must be 'Resident'.")
                        )

                # 🏢 Rule for Company customers
                elif rec.momentum_energy_customer_type == "COMPANY":
                    if not (rec.momentum_energy_industry or "").strip():
                        raise ValidationError(
                            _("Industry is required for Company customers.")
                        )

                    if not (rec.momentum_energy_entity_name or "").strip():
                        raise ValidationError(
                            _("Entity Name is required for Company customers.")
                        )

                    if not (rec.momentum_energy_abn_document_id or "").strip():
                        raise ValidationError(
                            _("ABN Number is required for Company customers.")
                        )


    @api.constrains(
    "momentum_energy_passport_id",
    "momentum_energy_passport_expiry",
    "momentum_energy_primary_country_of_birth",
    )
    def _check_country_of_birth_required(self):
        for rec in self:
            # ✅ Only validate when on Stage 4 and campaign is 'momentum'
            if (
                (str(rec.lead_stage) == "4" or getattr(rec.lead_stage, "id", None) == 4)
                and (rec.stage_2_campign_name or "").lower() == "momentum"
            ):
                has_passport = bool(
                    rec.momentum_energy_passport_id or rec.momentum_energy_passport_expiry
                )

                if has_passport and not rec.momentum_energy_primary_country_of_birth:
                    raise ValidationError(
                        _("Country of Birth is required when passport details are provided.")
                    )
 

    @api.constrains("momentum_energy_service_sub_type", "momentum_energy_service_start_date")
    def _check_service_start_date_required(self):
        for rec in self:
            # ✅ Validate only on Stage 4 and Momentum campaign
            if (
                (str(rec.lead_stage) == "4" or getattr(rec.lead_stage, "id", None) == 4)
                and (rec.stage_2_campign_name or "").lower() == "momentum"
            ):
                if (
                    rec.momentum_energy_service_sub_type
                    in ["MOVE IN", "NEW INSTALLATION"]
                    and not rec.momentum_energy_service_start_date
                ):
                    raise ValidationError(_(
                        "Service Start Date is required when Service Sub Type is 'Move In' or 'New Installation'."
                    ))


    @api.constrains(
    "en_concesion_card_holder",
    "momentum_energy_conc_card_type_code",
    "momentum_energy_conc_card_code",
    "momentum_energy_conc_card_number",
    "momentum_energy_conc_card_exp_date",
    "momentum_energy_card_first_name",
    "momentum_energy_card_last_name",
    "momentum_energy_conc_start_date",
    "momentum_energy_conc_end_date",
    "momentum_energy_concession_obtained",
    "momentum_energy_conc_has_ms",
    "momentum_energy_conc_in_grp_home",
    )
    def _check_concession_card_fields(self):
        for rec in self:
            # ✅ Run validation only for Stage 4 and Momentum campaign
            if (
                (str(rec.lead_stage) == "4" or getattr(rec.lead_stage, "id", None) == 4)
                and (rec.stage_2_campign_name or "").lower() == "momentum"
            ):
                if rec.en_concesion_card_holder == "yes":
                    required_fields = {
                        "momentum_energy_conc_card_type_code": "Card Type Code",
                        "momentum_energy_conc_card_code": "Concession Card Code",
                        "momentum_energy_conc_card_number": "Concession Card Number",
                        "momentum_energy_conc_card_exp_date": "Concession Card Expiry Date",
                        "momentum_energy_card_first_name": "Cardholder First Name",
                        "momentum_energy_card_last_name": "Cardholder Last Name",
                        "momentum_energy_conc_start_date": "Concession Start Date",
                        "momentum_energy_conc_end_date": "Concession End Date",
                        "momentum_energy_concession_obtained": "Concession Obtained",
                        "momentum_energy_conc_has_ms": "Medical Cooling Form Requirement",
                        "momentum_energy_conc_in_grp_home": "In Group Home",
                    }

                    # 🚨 Collect missing fields
                    missing = [
                        label
                        for field, label in required_fields.items()
                        if not getattr(rec, field)
                    ]

                    if missing:
                        raise ValidationError(_(
                            "The following fields are required when 'Concession Card Holder' is 'Yes':\n- %s"
                            % "\n- ".join(missing)
                        ))
                                    


    @api.constrains(
    "momentum_energy_customer_sub_type",
    "momentum_energy_passport_id",
    "momentum_energy_driving_license_id",
    "momentum_energy_medicare_id",
    )
    def _check_document_requirement(self):
        for rec in self:
            # ✅ Run validation only for Stage 4 and Momentum campaign
            if (
                (str(rec.lead_stage) == "4" or getattr(rec.lead_stage, "id", None) == 4)
                and (rec.stage_2_campign_name or "").strip().lower() == "momentum"
            ):
                # 🧩 Apply validation only for SME or RESIDENT customer subtypes
                if (rec.momentum_energy_customer_sub_type or "").upper() in ["SME", "RESIDENT"]:
                    has_passport = bool(rec.momentum_energy_passport_id)
                    has_license = bool(rec.momentum_energy_driving_license_id)
                    has_medicare = bool(rec.momentum_energy_medicare_id)

                    # 🚨 Raise error if no document is provided
                    if not (has_passport or has_license or has_medicare):
                        raise ValidationError(_(
                            "The following requirement must be met for SME and Resident customers "
                            "when Stage is 4 and Campaign is 'Momentum':\n\n"
                            "- At least one of the following must be provided:\n"
                            "  • Driving License Details\n"
                            "  • Passport Details\n"
                            "  • Medicare Card Details"
                        ))


               
    @api.constrains("stage_1_state", "nmi", "mirn")
    def _check_stage_1_energy_fields(self):
        """
        Validates NMI and MIRN based on state-specific rules
        Only runs when lead_for == 'energy_call_center'
        """

        for rec in self:
            # ✅ Validate only when lead_for == 'energy_call_center'
            if rec.lead_for != "energy_call_center" and rec.lead_stage != "1":
                continue


            state = rec.stage_1_state
            nmi = (rec.nmi or "").strip().upper()
            mirn = (rec.mirn or "").strip()

            # --------------------------
            # 🧩 NMI Validation
            # --------------------------


            # VIC: Starts with 6, alphanumeric 11 chars
            if state == "VIC":
                if not re.match(r"^[A-Z0-9]{11}$", nmi):
                    raise ValidationError(_("NMI for state VIC must be 11 alphanumeric characters."))
                if not nmi.startswith("6"):
                    raise ValidationError(_("NMI for state VIC must start with 6."))

            # NSW: Starts with 4, alphanumeric 11 chars
            elif state == "NSW":
                if not re.match(r"^[A-Z0-9]{11}$", nmi):
                    raise ValidationError(_("NMI for state NSW must be 11 alphanumeric characters."))
                if not nmi.startswith("4"):
                    raise ValidationError(_("NMI for state NSW must start with 4."))

            # QLD: Starts with 3 or QB
            elif state == "QLD":
                if not re.match(r"^[A-Z0-9]{11}$", nmi):
                    raise ValidationError(_("NMI for state QLD must be 11 alphanumeric characters."))
                if not (nmi.startswith("3") or nmi.startswith("QB")):
                    raise ValidationError(_("NMI for state QLD must start with 3 or QB."))

            # SA: Starts with 2
            elif state == "SA":
                if not re.match(r"^[A-Z0-9]{11}$", nmi):
                    raise ValidationError(_("NMI for state SA must be 11 alphanumeric characters."))
                if not nmi.startswith("2"):
                    raise ValidationError(_("NMI for state SA must start with 2."))

            # --------------------------
            # 🔢 MIRN Validation
            # --------------------------

            if mirn:
                if not mirn.isdigit() or len(mirn) != 11:
                    raise ValidationError(_("MIRN must be an 11-digit number."))
                if not mirn.startswith("5"):
                    raise ValidationError(_("MIRN must start with 5."))

    
    @api.constrains(
    "stage_2_state",
    "stage_2_concession_type",
    "stage_2_card_number",
    "stage_2_card_start_date",
    "stage_2_card_expiry_date",
    "lead_for",
    )
    def _check_stage_2_concession_card(self):
        """Validate concession card details for Stage 2 (Energy Call Center only)."""

        for rec in self:
            # ✅ Only validate for Stage 2 + Energy Call Center
            if rec.lead_for != "energy_call_center" or rec.lead_stage != "2":
                continue
            state = (rec.stage_2_state or "").strip().upper()
            card_type = (rec.stage_2_concession_type or "").strip()
            _logger.info("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm %s", card_type)
            card_no = (rec.stage_2_card_number or "").strip().upper()

            # Skip validation entirely if these key fields are missing
            if not state or not card_type or not card_no:
                continue

            # ---------------------------
            # 🟦 1. PCC / HCC / VCC
            # ---------------------------
            if card_type in ("PCC", "HCC", "VCC"):
                if state in ("VIC", "NSW", "QLD"):
                    pattern = r"^\d{9}[A-Z]$"
                    msg = "It must be 9 digits followed by 1 letter (e.g. 123456789A)."
                elif state == "SA":
                    pattern = r"^\d{10}[A-Z]$"
                    msg = "It must be 10 digits followed by 1 letter (e.g. 1234567890A)."
                else:
                    continue  # Unknown state → skip

                if not re.match(pattern, card_no):
                    raise ValidationError(_(f"Invalid {card_type} card number for State : {state}. {msg}"))

                # ✅ Start and Expiry Dates required
                if not rec.stage_2_card_start_date:
                    raise ValidationError(_(f"{card_type} Card Start Date is required for State : {state}."))
                if not rec.stage_2_card_expiry_date:
                    raise ValidationError(_(f"{card_type} Card Expiry Date is required for State : {state}."))

            # ---------------------------
            # 🟨 2. DVA (Gold Card)
            # ---------------------------
            elif card_type == "DVA Gold Card":
                # Card format: 3 letters + 5 digits (e.g. ABC12345)
                if not re.match(r"^[A-Z]{3}\d{5}$", card_no):
                    raise ValidationError(_("DVA card number must be 3 letters followed by 5 digits (e.g. ABC12345)."))

                if not rec.stage_2_card_expiry_date:
                    raise ValidationError(_("DVA card expiry date is required (format: MM/YY)."))

            # ---------------------------
            # 🟩 3. Others — skip validation
            # ---------------------------
            elif card_type == "OTHERS":
                continue

    @api.constrains(
        "stage_2_id_issuance_state",
        "stage_2_id_proof_type",
        "stage_2_licence_number",
        "stage_2_medicard_number",
        "stage_2_medicard_color",
        "stage_2_medicard_irn",
        "stage_2_passport_number",
        "stage_2_passport_issued_country",
        "stage_2_id_proof_name",
        "stage_2_id_number",
        "stage_2_id_start_date",
        "stage_2_id_expiry_date",
        "stage_2_dob",
        "lead_stage",
        "lead_for",
    )
    def _check_stage_2_id_proof(self):
        """Validate ID Proof details for Stage 2 (Energy Call Center)."""

        for rec in self:
            # ✅ Only validate for stage 2 and energy_call_center
            if not (rec.lead_for == "energy_call_center" and rec.lead_stage == "2"):
                continue

            state = (rec.stage_2_id_issuance_state or "").upper()
            id_type = (rec.stage_2_id_proof_type or "").lower()

            # -------------------------------------------------------
            # 🟦 DRIVER LICENCE VALIDATION
            # -------------------------------------------------------
            if id_type == "driver_licence":
                licence_no = (rec.stage_2_licence_number or "").strip().upper()

                licence_patterns = {
                    "VIC": {
                        "pattern": r"^0\d{8}$",
                        "hint": "Must start with 0 and be 9 digits total (e.g. 012345678).",
                    },
                    "NSW": {
                        "pattern": r"^(4\d{3}[A-Z]{2}|[0-9]{8})$",
                        "hint": "Must either be 4 digits + 2 letters (e.g. 4123AB) or an 8-digit number.",
                    },
                    "QLD": {
                        "pattern": r"^[01]\d{8}$",
                        "hint": "Must start with 0 or 1 and be 9 digits total (e.g. 012345678).",
                    },
                    "SA": {
                        "pattern": r"^[A-Z0-9]{6}$",
                        "hint": "Must be 6 characters long, letters or digits (e.g. A1B2C3).",
                    },
                }

                state_rule = licence_patterns.get(state)
                if not state_rule:
                    continue  # Skip unknown state

                if not licence_no:
                    raise ValidationError(_(f"Licence Number is required for {state}."))

                if not re.match(state_rule["pattern"], licence_no):
                    raise ValidationError(_(
                        f"Invalid Driver Licence Number for {state}. {state_rule['hint']}"
                    ))

                if not rec.stage_2_id_expiry_date:
                    raise ValidationError(_(
                        f"Driver Licence Expiry Date is required for {state}."
                    ))

            # -------------------------------------------------------
            # 🟩 MEDICARE CARD VALIDATION
            # -------------------------------------------------------
            elif id_type == "medicare_card":
                card_no = (rec.stage_2_medicard_number or "").strip()
                irn = (rec.stage_2_medicard_irn or "").strip()
                color = (rec.stage_2_medicard_color or "").capitalize()

                # Medicare card rules (same across states)
                if not card_no:
                    raise ValidationError(_("Medicare Card Number is required."))

                if not re.match(r"^\d{10}$", card_no):
                    raise ValidationError(_("Invalid Medicare Card Number. Must be exactly 10 digits."))

                if color not in ("Green", "Blue", "Yellow"):
                    raise ValidationError(_("Invalid Medicare Card Colour. Allowed values: Green, Blue, Yellow."))

                if not irn:
                    raise ValidationError(_("IRN (Individual Reference Number) is required for Medicare Card."))

                if not rec.stage_2_id_expiry_date:
                    raise ValidationError(_("Medicare Card Expiry Date (MM/YY) is required."))

            # -------------------------------------------------------
            # 🟨 PASSPORT VALIDATION
            # -------------------------------------------------------
            elif id_type == "passport":
                passport_no = (rec.stage_2_passport_number or "").strip().upper()
                issued_country = (rec.stage_2_passport_issued_country or "").strip().upper()

                if not passport_no:
                    raise ValidationError(_("Passport Number is required."))

                if not re.match(r"^[A-Z0-9]{6,9}$", passport_no):
                    raise ValidationError(_("Invalid Passport Number. Must be 6–9 alphanumeric characters."))

                if not issued_country:
                    raise ValidationError(_("Passport Issued Country is required."))

                if not rec.stage_2_id_start_date:
                    raise ValidationError(_("Passport Start Date (DD/MM/YYYY) is required."))

                if not rec.stage_2_id_expiry_date:
                    raise ValidationError(_("Passport Expiry Date (DD/MM/YYYY) is required."))

            # -------------------------------------------------------
            # 🟧 UNKNOWN ID TYPE — skip validation
            # -------------------------------------------------------
            else:
                continue  

    @api.constrains(
        "stage_2_dob",
    )
    def _check_stage_2_id_proof(self):
        """Validate ID Proof details for Stage 2 (Energy Call Center)."""

        for rec in self:
            # ✅ Only validate for Stage 2 and energy_call_center
            if not (rec.lead_for == "energy_call_center" and rec.lead_stage == "2"):
                continue

            # ✅ Validate Date of Birth (Must be 18 years or older)
            if rec.stage_2_dob:
                today = date.today()
                age_in_years = (today - rec.stage_2_dob).days / 365.25

                if age_in_years < 18:
                    raise ValidationError(_(
                        f"Applicant must be at least 18 years old. Current age: {int(age_in_years)} years."
                    ))
            else:
                raise ValidationError(_("Date of Birth (DOB) is required for Stage 2 ID proof validation."))            

    @api.constrains(
        "momentum_energy_service_state",
        "momentum_energy_service_post_code",
        "momentum_energy_primary_state",
        "momentum_energy_primary_post_code",
        "momentum_energy_primary_phone_mobile",
        "lead_stage",
        "stage_2_campign_name",
    )
    def _check_momentum_primary_details(self):
        for rec in self:
            # ✅ Apply validation only when stage=4 and campaign=momentum
            if rec.lead_stage != "4" or rec.stage_2_campign_name != "momentum":
                continue

            state = rec.momentum_energy_primary_state
            post_code = (rec.momentum_energy_primary_post_code or "").strip()
            mobile = (rec.momentum_energy_primary_phone_mobile or "").strip()

            # Define validation rules for Post Code (by State)
            post_code_rules = {
                "VIC": r"^3\d{3}$",  # Starts with 3 and has 4 digits
                "NSW": r"^2\d{3}$",
                "QLD": r"^4\d{3}$",
                "SA": r"^5\d{3}$",
            }

            # Validate Post Code (only for VIC, NSW, QLD, SA)
            if state in post_code_rules:
                pattern = post_code_rules[state]
                if not re.match(pattern, post_code):
                    raise ValidationError(
                        _(
                            f"Invalid Post Code for {state}. "
                            f"Expected format: starts with {pattern[1]} and must be 4 digits."
                        )
                    )

            # Validate Mobile Number — same for all states
            mobile_pattern = r"^04\d{8}$"  # Starts with 04, total 10 digits
            if mobile and not re.match(mobile_pattern, mobile):
                raise ValidationError(
                    _(
                        f"Invalid Mobile Number '{mobile}'. "
                        "It must start with '04' and contain 10 digits (e.g., 0412345678)."
                    )
                )  

    @api.constrains(
        "momentum_energy_service_state",
        "momentum_energy_service_post_code",
        "lead_stage",
        "stage_2_campign_name",
    )
    def _check_momentum_primary_details(self):
        for rec in self:
            # ✅ Apply validation only when stage=4 and campaign=momentum
            if rec.lead_stage != "4" or rec.stage_2_campign_name != "momentum":
                continue

            state = rec.momentum_energy_service_state
            post_code = (rec.momentum_energy_service_post_code or "").strip()
            # mobile = (rec.momentum_energy_primary_phone_mobile or "").strip()

            # Define validation rules for Post Code (by State)
            post_code_rules = {
                "VIC": r"^3\d{3}$",  # Starts with 3 and has 4 digits
                "NSW": r"^2\d{3}$",
                "QLD": r"^4\d{3}$",
                "SA": r"^5\d{3}$",
            }

            # Validate Post Code (only for VIC, NSW, QLD, SA)
            if state in post_code_rules:
                pattern = post_code_rules[state]
                if not re.match(pattern, post_code):
                    raise ValidationError(
                        _(
                            f"Invalid Service Post Code for {state}. "
                            f"Expected format: starts with {pattern[1]} and must be 4 digits."
                        )
                    )
                               
    @api.onchange('stage_2_campign_name')
    def _onchange_stage_2_campign_name(self):
        if self.stage_2_campign_name:
            campaign_dict = dict(self._fields['stage_2_campign_name'].selection)
            campaign_name = campaign_dict.get(self.stage_2_campign_name)
            dummy_text = """
                <p style='margin-top:8px; line-height:1.6;'>
                    <b>Selected Campaign:</b> {campaign_name}<br/><br/>
                    This campaign is currently active and includes multiple engagement
                    touchpoints such as calls, follow-ups, and automated messaging.
                    Our goal is to ensure clear communication and deliver a seamless
                    customer experience. Please review the script, guidelines, and
                    communication flow carefully before proceeding with any interaction.
                    Additional notes and instructions may be added by the team lead.
                </p>
                """
            self.campaign_notes = dummy_text.format(campaign_name=campaign_name)          
    
                            
    @api.model
    def _get_stage_sequence(self):
        """Return the ordered stages for the wizard navigation."""
        return ["1", "2", "3"]  # your lead_stage values

    def action_prev_stage(self):
        """Move to previous stage"""
        _logger.info("Previous button clicked for lead IDs: %s", self.ids)

        result = {}
        for lead in self:
            current_stage = int(lead.lead_stage or "1")

            if current_stage <= 1:
                _logger.warning("Lead %s already at minimum stage", lead.id)
                result = {"success": False, "error": "Already at first stage"}
            else:
                new_stage = str(current_stage - 1)
                lead.with_context(skip_stage_assign=True).write(
                    {"lead_stage": new_stage}
                )
                _logger.info(
                    "Lead %s moved from stage %s to %s",
                    lead.id,
                    current_stage,
                    new_stage,
                )
                result = {"success": True, "new_stage": new_stage}

        return result


    def action_next_stage(self):
        _logger.info("self is %s ", self)
        """Move to next stage"""
        _logger.info("Next button clicked for lead IDs: %s", self.ids)

        result = {}
        for lead in self:
            _logger.info("Lead current state is %s", lead.lead_stage)
            current_stage = int(lead.lead_stage or "1")

            if current_stage >= 3:
                _logger.warning("Lead %s already at maximum stage", lead.id)
                result = {"success": False, "error": "Already at last stage"}
                continue

            # Stage 1 → Stage 2
            if current_stage == 1:
                if (
                    lead.en_name
                    or lead.en_contact_number
                    or lead.cc_prefix
                    or lead.cc_first_name
                    or lead.in_current_address
                    or lead.in_current_provider
                ):
                    new_stage = "2"
                    lead.with_context(skip_stage_assign=True).write(
                        {"lead_stage": new_stage}
                    )
                    _logger.info(
                        "Lead current state after writing is %s", lead.lead_stage
                    )

                    _logger.info("Lead %s moved 1 → 2", lead.id)
                    result = {"success": True, "new_stage": new_stage}
                else:
                    result = {
                        "success": False,
                        "error": "Please fill required fields before moving to stage 2",
                    }

            # Stage 2 → Stage 3
            elif current_stage == 2:
                if lead.disposition == "sold_pending_quality":
                    new_stage = "3"
                    _logger.info(
                        "Lead current state after stage 2 wroting is %s",
                        lead.lead_stage,
                    )

                    lead.with_context(skip_stage_assign=True).write(
                        {"lead_stage": new_stage}
                    )
                    _logger.info("Lead %s moved 2 → 3", lead.id)
                    result = {"success": True, "new_stage": new_stage}
                else:
                    result = {
                        "success": False,
                        "error": "Please set disposition before moving to stage 3",
                    }

        return result

    @api.depends("services")
    def _compute_lead_for(self):
        for record in self:
            if record.services:
                record.lead_for = record.services
            else:
                record.lead_for = False

    # Core fields that trigger stage computation
    customer_name = fields.Char(string="Customer Name")
    customer_mobile_number = fields.Char(string="Customer Mobile Number")
    lead_for = fields.Char(
        string="Lead for", readonly=True, compute="_compute_lead_for", store=True
    )

    # Lead stage field - computed and stored
    lead_stage = fields.Selection(
        [
            ("1", "Stage 1"),
            ("2", "Stage 2"),
            ("3", "Stage 3"),
            ("4", "Stage 4"),
        ],
        string="Lead Current Stage : ",
        default="1",
        store=True,
        readonly=True,
    )



    en_current_address = fields.Char(string="Current Address")
    en_what_to_compare = fields.Selection(
        [
            ("electricity_gas", "Electricity & Gas"),
            ("electricity", "Elecricity"),
        ],
        string="What are you looking to compare?",
    )
    en_property_type = fields.Selection(
        [
            ("residential", "Residential"),
            ("business", "Business"),
        ],
        string="What type of property?",
    )
    en_moving_in = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Are you moving into this property?"
    )
    en_date = fields.Date("Date")
    en_property_ownership = fields.Selection(
        [
            ("own", "Own"),
            ("rent", "Rent"),
        ],
        string="Do you own or rent this property?",
    )
    en_usage_profile = fields.Selection(
        [
            (
                "low",
                "1-2 people, spemd minimal time at home, weekly washing, minimal heating, cooking.",
            ),
            (
                "medium",
                "3-4 people, home in the evening and weekend regular washing, heating and cooling.",
            ),
            (
                "high",
                "5+ people, home during the day, evenings and weekend daily washing, heating and cooling.",
            ),
        ],
        string="Usage Profile",
    )
    en_require_life_support = fields.Selection(
        [("no", "No"), ("yes", "Yes")],
        string="Does anyone residing or intending to reside at your premises require life support equipment?",
    )
    en_concesion_card_holder = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Are you a concession card holder?"
    )
    en_rooftop_solar = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Do you have rooftop solar panels :"
    )
    en_electricity_provider = fields.Selection(
        [
            ("1st_energy", "1st Energy"),
            ("actew_agl", "ActewAGL"),
            ("agl", "AGL"),
            ("alinta_energy", "Alinta Energy"),
            ("aus_power_gas", "Australian Power & Gas"),
            ("blue_nrg", "BlueNRG"),
            ("click_energy", "Click Energy"),
            ("dodo_energy", "Dodo Energy"),
            ("energy_australia", "Energy Australia"),
            ("lumo_energy", "Lumo Energy"),
            ("momentum_energy", "Momentum Energy"),
            ("neighbourhood", "Neighbourhood"),
            ("online_pow_gas", "Online Power & Gas"),
            ("origin", "Orgin"),
            ("people_energy", "People Energy"),
            ("power_direct", "Power Direct"),
            ("powershop", "Powershop"),
            ("q_energy", "QEnergy"),
            ("red_energy", "Red Energy"),
            ("simple_energy", "Simple Energy"),
            ("sumo_power", "Sumo Power"),
            ("tango_energy", "Tango Energy"),
            ("other", "Other/Unknown"),
        ],
        string="Who is your current electricity provider",
    )

    en_gas_provider = fields.Selection(
        [
            ("1st_energy", "1st Energy"),
            ("actew_agl", "ActewAGL"),
            ("agl", "AGL"),
            ("alinta_energy", "Alinta Energy"),
            ("aus_power_gas", "Australian Power & Gas"),
            ("blue_nrg", "BlueNRG"),
            ("click_energy", "Click Energy"),
            ("dodo_energy", "Dodo Energy"),
            ("energy_australia", "Energy Australia"),
            ("lumo_energy", "Lumo Energy"),
            ("momentum_energy", "Momentum Energy"),
            ("neighbourhood", "Neighbourhood"),
            ("online_pow_gas", "Online Power & Gas"),
            ("origin", "Orgin"),
            ("people_energy", "People Energy"),
            ("power_direct", "Power Direct"),
            ("powershop", "Powershop"),
            ("q_energy", "QEnergy"),
            ("red_energy", "Red Energy"),
            ("simple_energy", "Simple Energy"),
            ("sumo_power", "Sumo Power"),
            ("tango_energy", "Tango Energy"),
            ("other", "Other/Unknown"),
        ],
        "Who is your current gas provider",
    )
    en_name = fields.Char("Name", related="contact_name", readonly=False)
    en_contact_number = fields.Char("Contact Number", related="phone", readonly=False)
    en_customer_alt_phone = fields.Char(string="Customer Alt. Number")
    en_email = fields.Char("Email", related="email_normalized", readonly=False)
    en_request_callback = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Request a call back"
    )
    en_accpeting_terms = fields.Boolean(
        string="By submitting your details you agree that you have read and agreed to the Terms and Conditions and Privacy Policy."
    )
    stage_1_state = fields.Selection(
        [("VIC", "VIC"), ("NSW", "NSW"), ("QLD","QLD"), ("SA","SA")], string="State"
    )
    nmi = fields.Char(string="NMI")
    mirn = fields.Char(string="MIRN")
    frmp = fields.Char(string="FRMP")
    
    type_of_concession = fields.Selection(
        [("PCC", "PCC"), ("HCC", "HCC"), ("VCC", "VCC"),("DVA Gold Card", "DVA Gold Card"), ("others", "Others")],
        string="Type of Concession",
    )
    lead_agent_notes = fields.Text(string="Notes By Lead Agent")

    # Stage 2 fields
    stage_2_dob = fields.Date(string="Date of Birth")
    stage_2_id_issuance_state = fields.Selection(
        [("VIC", "VIC"), ("NSW", "NSW"), ("QLD","QLD"), ("SA","SA")], string="ID Issuance State"
    )
    stage_2_id_proof_type = fields.Selection(
        [
            ("driver_licence", "Driver Licence"),
            ("medicare_card", "Medicare Card"),
            ("passport", "Passport"),
        ],
        string="Type Of ID Proof",
        default="driver_licence",
    )
    stage_2_licence_number = fields.Char(string="License Number")
    stage_2_medicard_number = fields.Char(string="Card Number")
    stage_2_medicard_color = fields.Selection([("Green","Green"),("Blue","Blue"),("Yellow","Yellow")],string="Colour")
    stage_2_medicard_irn = fields.Char(string="IRN")
    stage_2_passport_number = fields.Char(string="Passport Number")
    stage_2_passport_issued_country = fields.Char(string="Issued Country")
    stage_2_id_proof_name = fields.Char(string="Name on ID Proof")
    stage_2_id_number = fields.Char(string="ID Number")
    stage_2_id_start_date = fields.Date(string="ID Start Date")
    stage_2_id_expiry_date = fields.Date(string="ID Expire date")



    stage_2_state = fields.Selection(
        [("VIC", "VIC"), ("NSW", "NSW"), ("QLD","QLD"), ("SA","SA")], string="State"
    )
    stage_2_concession_type = fields.Selection(
        [("PCC", "PCC"), ("HCC", "HCC"), ("VCC", "VCC"), ("DVA Gold Card", "DVA Gold Card"),("others", "Others")],
        string="Type of Concession",
        related="type_of_concession",
        readonly=False,
    )
    stage_2_card_number = fields.Char(string="Concession Card Number")
    stage_2_card_holder_name = fields.Char(string="Concession Card Holder Name")
    stage_2_card_type = fields.Char(string="Concession Card Type")
    stage_2_card_start_date = fields.Date(string="Concession Card Start Date")
    stage_2_card_expiry_date = fields.Date(string="Concession Card Expiry Date")
    stage_2_sec_acc_holder = fields.Char(string="Secondary Account Holder Name")
    stage_2_sec_acc_holder_dob = fields.Date(string="Secondary Account Holder DOB")
    stage_2_sec_acc_holder_mobile = fields.Char(
        string="Secondary Account Holder Mobile"
    )
    stage_2_sec_acc_holder_email = fields.Char(string="Secondary Account Holder Email")
    stage_2_bill = fields.Selection(
        [("postal", "Postal"), ("email", "Email")], string="Bill", default="postal"
    )
    stage_2_dnc = fields.Char(string="DNC")
    stage_2_lead_agent = fields.Char(string="Lead Agent")
    stage_2_head_transfer_name = fields.Char(string="Head Transfer Name")
    stage_2_closer_name = fields.Char(string="Closer Name")
    stage_2_sale_date = fields.Date(string="Sale Date")
    stage_2_campign_name = fields.Selection(
        [
            ("dodo_power_gas", "DODO Power & Gas"),
            ("first_energy", "1st energy"),
            ("momentum", "Momentum"),
        ],
        string="Campign Name",
        default="dodo_power_gas",
    )
    stage_2_lead_source = fields.Char(string="Lead Source")
    stage_2_lead_agent_notes = fields.Text(string="Notes By Lead Agent")
    disposition = fields.Selection(
        [
            ("callback", "Callback"),
            ("lost", "Lost"),
            ("sold_pending_quality", "Sold – Pending Quality"),
        ],
        string="Disposition",
    )
    callback_date = fields.Datetime("Callback Date")
    campaign_notes = fields.Html(string="Campaign Notes", readonly=True)

    # FIRST ENERGY FIELDS
    internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    existing_sale = fields.Char(string="Existing Sale with NMI & Phone Number")
    online_enquiry_form = fields.Char(string="Online Enquiry Form")
    vendor_id = fields.Char(string="Vendor ID", default="Utility Hub")
    agent = fields.Char(string="Agent")
    channel_ref = fields.Char(string="Channel Reference")
    sale_ref = fields.Char(string="Sale Reference")
    lead_ref = fields.Char(string="Lead Ref (External)")  # renamed to avoid clash
    incentive = fields.Char(string="Incentive")
    sale_date = fields.Date(string="Date of Sale")
    campaign_ref = fields.Char(string="Campaign Reference")
    promo_code = fields.Char(string="Promo Code")
    current_elec_retailer = fields.Selection(
        [
            ("1st_energy", "1st Energy"),
            ("actew_agl", "ActewAGL"),
            ("agl", "AGL"),
            ("alinta_energy", "Alinta Energy"),
            ("aus_power_gas", "Australian Power & Gas"),
            ("blue_nrg", "BlueNRG"),
            ("click_energy", "Click Energy"),
            ("dodo_energy", "Dodo Energy"),
            ("energy_australia", "Energy Australia"),
            ("lumo_energy", "Lumo Energy"),
            ("momentum_energy", "Momentum Energy"),
            ("neighbourhood", "Neighbourhood"),
            ("online_pow_gas", "Online Power & Gas"),
            ("origin", "Orgin"),
            ("people_energy", "People Energy"),
            ("power_direct", "Power Direct"),
            ("powershop", "Powershop"),
            ("q_energy", "QEnergy"),
            ("red_energy", "Red Energy"),
            ("simple_energy", "Simple Energy"),
            ("sumo_power", "Sumo Power"),
            ("tango_energy", "Tango Energy"),
            ("other", "Other/Unknown"),
        ],
        string="Current Electric Retailer",
    )
    current_gas_retailer = fields.Selection(
        [
            ("1st_energy", "1st Energy"),
            ("actew_agl", "ActewAGL"),
            ("agl", "AGL"),
            ("alinta_energy", "Alinta Energy"),
            ("aus_power_gas", "Australian Power & Gas"),
            ("blue_nrg", "BlueNRG"),
            ("click_energy", "Click Energy"),
            ("dodo_energy", "Dodo Energy"),
            ("energy_australia", "Energy Australia"),
            ("lumo_energy", "Lumo Energy"),
            ("momentum_energy", "Momentum Energy"),
            ("neighbourhood", "Neighbourhood"),
            ("online_pow_gas", "Online Power & Gas"),
            ("origin", "Orgin"),
            ("people_energy", "People Energy"),
            ("power_direct", "Power Direct"),
            ("powershop", "Powershop"),
            ("q_energy", "QEnergy"),
            ("red_energy", "Red Energy"),
            ("simple_energy", "Simple Energy"),
            ("sumo_power", "Sumo Power"),
            ("tango_energy", "Tango Energy"),
            ("other", "Other/Unknown"),
        ],
        string="Current Gas Retailer",
    )
    multisite = fields.Boolean(string="Multisite")
    existing_customer = fields.Boolean(string="Existing Customer")
    customer_account_no = fields.Char(string="Customer Account Number")
    customer_type = fields.Selection(
        [
            ("resident", "Resident"),
            ("company", "Company"),
        ],
        string="Customer Type",
        default="resident",
    )
    account_name = fields.Char(string="Account Name")
    abn = fields.Char(string="ABN")
    acn = fields.Char(string="ACN")
    business_name = fields.Char(string="Business Name")
    trustee_name = fields.Char(string="Trustee Name")
    trading_name = fields.Char(string="Trading Name")
    position = fields.Char(string="Position")
    sale_type = fields.Selection(
        [("transfer", "Transfer"), ("movein", "Movein")],
        string="Sale Type",
        default="transfer",
    )
    customer_title = fields.Char(string="Title")
    first_name = fields.Char(
        string="First Name", related="contact_name", readonly=False
    )
    last_name = fields.Char(string="Last Name")
    phone_landline = fields.Char(string="Phone Landline")
    phone_mobile = fields.Char(string="Mobile Number", related="phone", readonly=False)
    auth_date_of_birth = fields.Date(
        string="Authentication Date of Birth", related="stage_2_dob", readonly=False
    )
    auth_expiry = fields.Date(string="Authentication Expiry")
    auth_no = fields.Char(string="Authentication No")
    auth_type = fields.Char(string="Authentication Type")
    email = fields.Char(string="Email", related="email_normalized", readonly=False)
    life_support = fields.Selection(
        [("no", "No"), ("yes", "Yes")],
        string="Life Support",
        related="en_require_life_support",
        readonly=False,
    )
    concessioner_number = fields.Char(
        string="Concessioner Number", related="stage_2_card_number", readonly=False
    )
    concession_expiry = fields.Date(
        string="Concession Expiry Date",
        related="stage_2_card_expiry_date",
        readonly=False,
    )
    concession_flag = fields.Boolean(string="Concession Flag", default=False)
    concession_start_date = fields.Date(
        string="Concession Start Date",
        related="stage_2_card_start_date",
        readonly=False,
    )
    concession_type = fields.Selection(
        [("pcc", "PCC"), ("hcc", "HCC"), ("vcc", "VCC"), ("others", "Others")],
        string="Concession Type",
        related="stage_2_concession_type",
        readonly=False,
    )
    conc_first_name = fields.Char(
        string="Concession First Name",
        related="stage_2_card_holder_name",
        readonly=False,
    )
    conc_last_name = fields.Char(string="Concession Last Name")
    secondary_title = fields.Char(string="Secondary Title")
    sec_first_name = fields.Char(
        string="Secondary First Name", related="stage_2_sec_acc_holder", readonly=False
    )
    sec_last_name = fields.Char(string="Secondary Last Name")
    sec_auth_date_of_birth = fields.Date(
        string="Secondary Authentication DOB",
        related="stage_2_sec_acc_holder_dob",
        readonly=False,
    )
    sec_auth_no = fields.Char(string="Secondary Authentication No")
    sec_auth_type = fields.Char(string="Secondary Authentication Type")
    sec_auth_expiry = fields.Date(string="Secondary Authentication Expiry")
    sec_email = fields.Char(
        string="Secondary Email", related="stage_2_sec_acc_holder_email", readonly=False
    )
    sec_phone_home = fields.Char(string="Secondary Phone Home")
    sec_mobile_number = fields.Char(
        string="Secondary Mobile Number",
        related="stage_2_sec_acc_holder_mobile",
        readonly=False,
    )
    site_apartment_no = fields.Char(string="Site Apartment Number")
    site_apartment_type = fields.Char(string="Site Apartment Type")
    site_building_name = fields.Char(string="Site Building Name")
    site_floor_no = fields.Char(string="Site Floor Number")
    site_floor_type = fields.Char(string="Site Floor Type")
    site_location_description = fields.Text(string="Site Location Description")
    site_lot_number = fields.Char(string="Site Lot Number")
    site_street_number = fields.Char(string="Site Street Number")
    site_street_name = fields.Char(string="Site Street Name")
    site_street_number_suffix = fields.Char(string="Site Street Number Suffix")
    site_street_type = fields.Char(string="Site Street Type")
    site_street_suffix = fields.Char(string="Site Street Suffix")
    site_suburb = fields.Char(string="Site Suburb")
    site_state = fields.Char(string="Site State")
    site_post_code = fields.Char(string="Site Post Code")
    gas_site_apartment_number = fields.Char(string="Gas Site Apartment Number")
    gas_site_apartment_type = fields.Char(string="Gas Site Apartment Type")
    gas_site_building_name = fields.Char(string="Gas Site Building Name")
    gas_site_floor_number = fields.Char(string="Gas Site Floor Number")
    gas_site_floor_type = fields.Char(string="Gas Site Floor Type")
    gas_site_location_description = fields.Char(string="Gas Site Location Description")
    gas_site_lot_number = fields.Char(string="Gas Site Lot Number")
    gas_site_street_name = fields.Char(string="Gas Site Street Name")
    gas_site_street_number = fields.Char(string="Gas Site Street Number")
    gas_site_street_number_suffix = fields.Char(
        string="Gas Site Street Number Suffix"
    )  # typo fixed
    gas_site_street_type = fields.Char(string="Gas Site Street Type")
    gas_site_street_suffix = fields.Char("Gas Site Street Suffix")
    gas_site_suburb = fields.Char("Gas Site Suburb")
    gas_site_state = fields.Char("Gas Site State")
    gas_site_post_code = fields.Char("Gas Site Post Code")
    network_tariff_code = fields.Char("Network Tariff Code")
    nmi = fields.Char("NMI")
    mirn = fields.Char("MIRN")
    fuel = fields.Char("Fuel")
    feed_in = fields.Char("Feed In")
    annual_usage = fields.Float("Annual Usage")
    gas_annual_usage = fields.Float("Gas Annual Usage")
    product_code = fields.Char("Product Code")
    gas_product_code = fields.Char("Gas Product Code")
    offer_description = fields.Text("Offer Description")
    gas_offer_description = fields.Text("Gas Offer Description")
    green_percent = fields.Float("Green Percent")
    proposed_transfer_date = fields.Date("Proposed Transfer Date")
    gas_proposed_transfer_date = fields.Date("Gas Proposed Transfer Date")
    bill_cycle_code = fields.Char("Bill Cycle Code")
    gas_bill_cycle_code = fields.Char("Gas Bill Cycle Code")
    average_monthly_spend = fields.Float("Average Monthly Spend")
    is_owner = fields.Selection([("no", "No"), ("yes", "Yes")], string="Is Owner")
    has_accepted_marketing = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Has Accepted Marketing"
    )
    email_account_notice = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Email Account Notice"
    )
    email_invoice = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Email Invoice"
    )
    billing_email = fields.Char("Billing Email")
    postal_building_name = fields.Char("Postal Building Name")
    postal_apartment_number = fields.Char("Postal Apartment Number")
    postal_apartment_type = fields.Char("Postal Apartment Type")
    postal_floor_number = fields.Char("Postal Floor Number")
    postal_floor_type = fields.Char("Postal Floor Type")
    postal_lot_no = fields.Char("Postal Lot No")
    postal_street_number = fields.Char("Postal Street Number")
    postal_street_number_suffix = fields.Char("Postal Street Number Suffix")
    postal_street_name = fields.Char("Postal Street Name")
    postal_street_type = fields.Char("Postal Street Type")
    postal_street_suffix = fields.Char("Postal Street Suffix")
    postal_suburb = fields.Char("Postal Suburb")
    postal_post_code = fields.Char("Postal Post Code")
    postal_state = fields.Char("Postal State")
    comments = fields.Text("Comments")
    transfer_special_instructions = fields.Text("Transfer Special Instructions")
    medical_cooling = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Medical Cooling"
    )
    medical_cooling_energy_rebate = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Medical Cooling Energy Rebate"
    )
    benefit_end_date = fields.Date("Benefit End Date")
    sales_class = fields.Char("Sales Class")
    bill_group_code = fields.Char("Bill Group Code")
    gas_meter_number = fields.Char("Gas Meter Number")
    centre_name = fields.Char("Centre Name")
    qc_name = fields.Char("QC Name")
    verifiers_name = fields.Char("Verifier’s Name")
    tl_name = fields.Char("TL Name")
    dnc_ref_no = fields.Char("DNC Ref No")
    audit_2 = fields.Char("Audit-2")
    welcome_call = fields.Boolean("Welcome Call")
    stage_3_dispostion = fields.Selection(
        [
            ("closed", "Sale Closed"),
            ("on_hold", "Sale QA Hold"),
            ("failed", "Sale QA Failed"),
        ],
        string="Disposition by QA Team",
    )
    lost_reason = fields.Char(string="Remarks")
    qa_notes = fields.Char("Notes by QA")

    # DODO POWER AND GAS
    dp_internal_dnc_checked = fields.Date(string="Internal DNC Checked")
    dp_existing_sale = fields.Char(
        string="Existing Sale with NMI & Phone Number (Internal)"
    )
    dp_online_enquiry_form = fields.Char(string="Online Enquiry Form")
    dp_sales_name = fields.Char(string="Sales Name")
    dp_sales_reference = fields.Char(string="Sales Reference")
    dp_agreement_date = fields.Date(string="Agreement Date")
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
    dp_prev_addr_1 = fields.Char(string="Previous Address Line 1")
    dp_prev_addr_2 = fields.Char(string="Previous Address Line 2")
    dp_prev_addr_state = fields.Char(string="Previous Address State")
    dp_prev_addr_postcode = fields.Char(string="Previous Address Postcode")
    dp_billing_address = fields.Boolean(string="Billing Address")
    dp_bill_addr_1 = fields.Char(string="Bill Address Line 1")
    dp_bill_addr_2 = fields.Char(string="Bill Address Line 2")
    dp_bill_addr_state = fields.Char(string="Bill Address State")
    dp_bill_addr_postcode = fields.Char(string="Bill Address Postcode")
    dp_concession = fields.Boolean(string="Concession")
    dp_concession_card_type = fields.Char(string="Concession Card Type")
    dp_concession_card_no = fields.Char(string="Concession Card No")
    dp_concession_start_date = fields.Date(string="Concession Start Date")
    dp_concession_exp_date = fields.Date(string="Concession Expiry Date")
    dp_concession_first_name = fields.Char(string="Concession First Name")
    dp_concession_middle_name = fields.Char(string="Concession Middle Name")
    dp_concession_last_name = fields.Char(string="Concession Last Name")
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
    dp_invoice_method = fields.Selection(
        [("email", "Email"), ("post", "Post"), ("sms", "SMS")], string="Invoice Method"
    )
    dp_customer_salutation = fields.Char(string="Customer Salutation")
    dp_first_name = fields.Char(
        string="First Name", related="contact_name", readonly=False
    )
    dp_last_name = fields.Char(string="Last Name")
    dp_date_of_birth = fields.Date(
        string="Date of Birth", related="stage_2_dob", readonly=False
    )
    dp_email_contact = fields.Char(
        string="Email Contact", related="email_normalized", readonly=False
    )
    dp_contact_number = fields.Char(
        string="Contact Number", related="phone", readonly=False
    )
    dp_hearing_impaired = fields.Boolean(string="Hearing Impaired", default=False)
    dp_secondary_contact = fields.Boolean(string="Secondary Contact", default=False)
    dp_secondary_salutation = fields.Char(string="Secondary Salutation")
    dp_secondary_first_name = fields.Char(
        string="Secondary First Name", realted="stage_2_sec_acc_holder", readonly=False
    )
    dp_secondary_last_name = fields.Char(string="Secondary Last Name")
    dp_secondary_date_of_birth = fields.Date(
        string="Secondary Date of Birth",
        realted="stage_2_sec_acc_holder_dob",
        readonly=False,
    )
    dp_secondary_email = fields.Char(
        string="Secondary Email", realted="stage_2_sec_acc_holder_email", readonly=False
    )
    dp_referral_code = fields.Char(string="Referral Code")
    dp_new_username = fields.Char(string="New Username")
    dp_new_password = fields.Char(string="New Password")
    dp_customer_dlicense = fields.Char(string="Driver License")
    dp_customer_dlicense_state = fields.Char(string="DL State")
    dp_customer_dlicense_exp = fields.Date(string="DL Expiry")
    dp_customer_passport = fields.Char(string="Passport")
    dp_customer_passport_exp = fields.Date(string="Passport Expiry")
    dp_customer_medicare = fields.Char(string="Medicare")
    dp_customer_medicare_ref = fields.Char(string="Medicare Ref")
    dp_position_at_current_employer = fields.Char(string="Position at Current Employer")
    dp_employment_status = fields.Char(string="Employment Status")
    dp_current_employer = fields.Char(string="Current Employer")
    dp_employer_contact_number = fields.Char(string="Employer Contact Number")
    dp_years_in_employment = fields.Integer(string="Years in Employment")
    dp_months_in_employment = fields.Integer(string="Months in Employment")
    dp_employment_confirmation = fields.Boolean(string="Employment Confirmation")
    dp_life_support = fields.Boolean(string="Life Support", default=False)
    dp_life_support_machine_type = fields.Char(string="Life Support Machine Type")
    dp_life_support_details = fields.Text(string="Life Support Details")
    dp_nmi = fields.Char(string="NMI")
    dp_nmi_source = fields.Char(string="NMI Source")
    dp_mirn = fields.Char(string="MIRN")
    dp_mirn_source = fields.Char(string="MIRN Source")
    dp_connection_date = fields.Date(string="Connection Date")
    dp_electricity_connection = fields.Boolean(string="Electricity Connection")
    dp_gas_connection = fields.Boolean(string="Gas Connection")
    dp_12_month_disconnection = fields.Boolean(string="12 Month Disconnection")
    dp_cert_electrical_safety = fields.Boolean(string="Electrical Safety Cert")
    dp_cert_electrical_safety_id = fields.Char(string="Cert Electrical Safety ID")
    dp_cert_electrical_safety_sent = fields.Boolean(string="Cert Sent")
    dp_explicit_informed_consent = fields.Boolean(string="Explicit Informed Consent")
    dp_center_name = fields.Char(string="Center Name", default="Utility Hub")
    dp_closer_name = fields.Char(string="Closer Name")
    dp_dnc_wash_number = fields.Char(string="DNC Wash Number")
    dp_dnc_exp_date = fields.Date(string="DNC Exp Date")
    dp_audit_1 = fields.Char(string="Audit-1")
    dp_audit_2 = fields.Char(string="Audit-2")
    dp_welcome_call = fields.Boolean(string="Welcome Call")

    # MOMENTUM ENERGY FORM
    momentum_energy_transaction_reference = fields.Char(
        "Sale Ref Number"
    )
    momentum_energy_transaction_channel = fields.Char(
        "Transaction Channel"
    )
    momentum_energy_transaction_date = fields.Datetime(
        "Transaction Date"
    )
    momentum_energy_transaction_verification_code = fields.Char(
        "Transaction Verification Code"
    )
    momentum_energy_transaction_source = fields.Char(
        "Transaction Source", default="EXTERNAL", readonly=True
    )

    momentum_energy_customer_type = fields.Selection(
        [("RESIDENT", "Resident"), ("COMPANY", "Company")],
        string="Customer Type",
    )

    momentum_energy_customer_sub_type = fields.Selection(
        [
            ("RESIDENT", "Resident"),
            ("Incorporation", "Incorporation"),
            ("Limited Company", "Limited Company"),
            ("NA", "NA"),
            ("Partnership", "Partnership"),
            ("Private", "Private"),
            ("Sole Trader", "Sole Trader"),
            ("Trust", "Trust"),
            ("C&I", "C&I"),
            ("SME", "SME"),
        ],
        string="Customer Sub Type",
    )
    momentum_energy_communication_preference = fields.Selection(
        [("EMAIL", "Email"), ("PHONE", "Phone")],
        string="Communication Preference",
    )
    momentum_energy_promotion_allowed = fields.Boolean(
        "Promotion Allowed", default=True
    )
    momentum_energy_passport_id = fields.Char("Passport Number")
    momentum_energy_passport_expiry = fields.Date("Passport Expiry Date")
    momentum_energy_passport_country = fields.Char(
        "Passport Issuing Country"
    )
    momentum_energy_driving_license_id = fields.Char(
        "Driving License Number"
    )
    momentum_energy_driving_license_expiry = fields.Date(
        "Driving License Expiry Date"
    )
    momentum_energy_driving_license_state = fields.Selection(
        [
            ("NSW", "NSW"),
            ("VIC", "VIC"),
            ("QLD", "QLD"),
            ("WA", "WA"),
            ("SA", "SA"),
            ("TAS", "TAS"),
            ("ACT", "ACT"),
            ("NT", "NT"),
        ],
        string="Issuing State",
    )
    momentum_energy_medicare_id = fields.Char("Medicare Number")
    momentum_energy_medicare_number = fields.Char(
        "Medicare Document Number"
    )
    momentum_energy_medicare_expiry = fields.Date("Medicare Expiry Date")
    momentum_energy_industry = fields.Selection(
        [
            ("Agriculture", "Agriculture"),
            ("Apparel", "Apparel"),
            ("Banking", "Banking"),
            ("Biotechnology", "Biotechnology"),
            ("Chemicals", "Chemicals"),
            ("Communications", "Communications"),
            ("Construction", "Construction"),
            ("Consulting", "Consulting"),
            ("Education", "Education"),
            ("Electronics", "Electronics"),
            ("Energy", "Energy"),
            ("Engineering", "Engineering"),
            ("Entertainment", "Entertainment"),
            ("Environmental", "Environmental"),
            ("Finance", "Finance"),
            ("Food & Beverage", "Food & Beverage"),
            ("Government", "Government"),
            ("Healthcare", "Healthcare"),
            ("Hospitality", "Hospitality"),
            ("Insurance", "Insurance"),
            ("Machinery", "Machinery"),
            ("Manufacturing", "Manufacturing"),
            ("Media", "Media"),
            ("Not For Profit", "Not For Profit"),
            ("Other", "Other"),
            ("Recreation", "Recreation"),
            ("Retail", "Retail"),
            ("Shipping", "Shipping"),
            ("Technology", "Technology"),
            ("Telecommunications", "Telecommunications"),
            ("Transportation", "Transportation"),
            ("Utilities", "Utilities"),
        ],
        string="Industry",
    )

    momentum_energy_entity_name = fields.Char("Entity Name")
    momentum_energy_trading_name = fields.Char("Trading Name")
    momentum_energy_trustee_name = fields.Char("Trustee Name")
    momentum_energy_abn_document_id = fields.Char("ABN Document ID")
    momentum_energy_acn_document_id = fields.Char("ACN Document ID")
    momentum_energy_primary_contact_type = fields.Char(
        "Contact Type", default="PRIMARY",readonly=True
    )
    momentum_energy_primary_salutation = fields.Selection(
        [
            ("Mr.", "Mr."),
            ("Mrs.", "Mrs."),
            ("Ms.", "Ms."),
            ("Dr.", "Dr."),
            ("Prof.", "Prof."),
        ],
        string="Salutation",
    )
    momentum_energy_primary_first_name = fields.Char(
        "First Name", related="contact_name", readonly=False
    )
    momentum_energy_primary_middle_name = fields.Char("Middle Name")
    momentum_energy_primary_last_name = fields.Char("Last Name")
    momentum_energy_primary_country_of_birth = fields.Selection([
        ("AFG", "AFG"), ("ALA", "ALA"), ("ALB", "ALB"), ("DZA", "DZA"),
        ("ASM", "ASM"), ("AND", "AND"), ("AGO", "AGO"), ("AIA", "AIA"),
        ("ATA", "ATA"), ("ATG", "ATG"), ("ARG", "ARG"), ("ARM", "ARM"),
        ("ABW", "ABW"), ("AUS", "AUS"), ("AUT", "AUT"), ("AZE", "AZE"),
        ("BHS", "BHS"), ("BHR", "BHR"), ("BGD", "BGD"), ("BRB", "BRB"),
        ("BLR", "BLR"), ("BEL", "BEL"), ("BLZ", "BLZ"), ("BEN", "BEN"),
        ("BMU", "BMU"), ("BTN", "BTN"), ("BOL", "BOL"), ("BES", "BES"),
        ("BIH", "BIH"), ("BWA", "BWA"), ("BVT", "BVT"), ("BRA", "BRA"),
        ("IOT", "IOT"), ("UMI", "UMI"), ("VGB", "VGB"), ("VIR", "VIR"),
        ("BRN", "BRN"), ("BGR", "BGR"), ("BFA", "BFA"), ("BDI", "BDI"),
        ("KHM", "KHM"), ("CMR", "CMR"), ("CAN", "CAN"), ("CPV", "CPV"),
        ("CYM", "CYM"), ("CAF", "CAF"), ("TCD", "TCD"), ("CHL", "CHL"),
        ("CHN", "CHN"), ("CXR", "CXR"), ("CCK", "CCK"), ("COL", "COL"),
        ("COM", "COM"), ("COG", "COG"), ("COD", "COD"), ("COK", "COK"),
        ("CRI", "CRI"), ("HRV", "HRV"), ("CUB", "CUB"), ("CUW", "CUW"),
        ("CYP", "CYP"), ("CZE", "CZE"), ("DNK", "DNK"), ("DJI", "DJI"),
        ("DMA", "DMA"), ("DOM", "DOM"), ("ECU", "ECU"), ("EGY", "EGY"),
        ("SLV", "SLV"), ("GNQ", "GNQ"), ("ERI", "ERI"), ("EST", "EST"),
        ("ETH", "ETH"), ("FLK", "FLK"), ("FRO", "FRO"), ("FJI", "FJI"),
        ("FIN", "FIN"), ("FRA", "FRA"), ("GUF", "GUF"), ("PYF", "PYF"),
        ("ATF", "ATF"), ("GAB", "GAB"), ("GMB", "GMB"), ("GEO", "GEO"),
        ("DEU", "DEU"), ("GHA", "GHA"), ("GIB", "GIB"), ("GRC", "GRC"),
        ("GRL", "GRL"), ("GRD", "GRD"), ("GLP", "GLP"), ("GUM", "GUM"),
        ("GTM", "GTM"), ("GGY", "GGY"), ("GIN", "GIN"), ("GNB", "GNB"),
        ("GUY", "GUY"), ("HTI", "HTI"), ("HMD", "HMD"), ("VAT", "VAT"),
        ("HND", "HND"), ("HKG", "HKG"), ("HUN", "HUN"), ("ISL", "ISL"),
        ("IND", "IND"), ("IDN", "IDN"), ("CIV", "CIV"), ("IRN", "IRN"),
        ("IRQ", "IRQ"), ("IRL", "IRL"), ("IMN", "IMN"), ("ISR", "ISR"),
        ("ITA", "ITA"), ("JAM", "JAM"), ("JPN", "JPN"), ("JEY", "JEY"),
        ("JOR", "JOR"), ("KAZ", "KAZ"), ("KEN", "KEN"), ("KIR", "KIR"),
        ("KWT", "KWT"), ("KGZ", "KGZ"), ("LAO", "LAO"), ("LVA", "LVA"),
        ("LBN", "LBN"), ("LSO", "LSO"), ("LBR", "LBR"), ("LBY", "LBY"),
        ("LIE", "LIE"), ("LTU", "LTU"), ("LUX", "LUX"), ("MAC", "MAC"),
        ("MKD", "MKD"), ("MDG", "MDG"), ("MWI", "MWI"), ("MYS", "MYS"),
        ("MDV", "MDV"), ("MLI", "MLI"), ("MLT", "MLT"), ("MHL", "MHL"),
        ("MTQ", "MTQ"), ("MRT", "MRT"), ("MUS", "MUS"), ("MYT", "MYT"),
        ("MEX", "MEX"), ("FSM", "FSM"), ("MDA", "MDA"), ("MCO", "MCO"),
        ("MNG", "MNG"), ("MNE", "MNE"), ("MSR", "MSR"), ("MAR", "MAR"),
        ("MOZ", "MOZ"), ("MMR", "MMR"), ("NAM", "NAM"), ("NRU", "NRU"),
        ("NPL", "NPL"), ("NLD", "NLD"), ("NCL", "NCL"), ("NZL", "NZL"),
        ("NIC", "NIC"), ("NER", "NER"), ("NGA", "NGA"), ("NIU", "NIU"),
        ("NFK", "NFK"), ("PRK", "PRK"), ("MNP", "MNP"), ("NOR", "NOR"),
        ("OMN", "OMN"), ("PAK", "PAK"), ("PLW", "PLW"), ("PSE", "PSE"),
        ("PAN", "PAN"), ("PNG", "PNG"), ("PRY", "PRY"), ("PER", "PER"),
        ("PHL", "PHL"), ("PCN", "PCN"), ("POL", "POL"), ("PRT", "PRT"),
        ("PRI", "PRI"), ("QAT", "QAT"), ("UNK", "UNK"), ("REU", "REU"),
        ("ROU", "ROU"), ("RUS", "RUS"), ("RWA", "RWA"), ("BLM", "BLM"),
        ("SHN", "SHN"), ("KNA", "KNA"), ("LCA", "LCA"), ("MAF", "MAF"),
        ("SPM", "SPM"), ("VCT", "VCT"), ("WSM", "WSM"), ("SMR", "SMR"),
        ("STP", "STP"), ("SAU", "SAU"), ("SEN", "SEN"), ("SRB", "SRB"),
        ("SYC", "SYC"), ("SLE", "SLE"), ("SGP", "SGP"), ("SXM", "SXM"),
        ("SVK", "SVK"), ("SVN", "SVN"), ("SLB", "SLB"), ("SOM", "SOM"),
        ("ZAF", "ZAF"), ("SGS", "SGS"), ("KOR", "KOR"), ("SSD", "SSD"),
        ("ESP", "ESP"), ("LKA", "LKA"), ("SDN", "SDN"), ("SUR", "SUR"),
        ("SJM", "SJM"), ("SWZ", "SWZ"), ("SWE", "SWE"), ("CHE", "CHE"),
        ("SYR", "SYR"), ("TWN", "TWN"), ("TJK", "TJK"), ("TZA", "TZA"),
        ("THA", "THA"), ("TLS", "TLS"), ("TGO", "TGO"), ("TKL", "TKL"),
        ("TON", "TON"), ("TTO", "TTO"), ("TUN", "TUN"), ("TUR", "TUR"),
        ("TKM", "TKM"), ("TCA", "TCA"), ("TUV", "TUV"), ("UGA", "UGA"),
        ("UKR", "UKR"), ("ARE", "ARE"), ("GBR", "GBR"), ("USA", "USA"),
        ("URY", "URY"), ("UZB", "UZB"), ("VUT", "VUT"), ("VEN", "VEN"),
        ("VNM", "VNM"), ("WLF", "WLF"), ("ESH", "ESH"), ("YEM", "YEM"),
        ("ZMB", "ZMB"), ("ZWE", "ZWE"),
    ],string="Country of Birth")
    momentum_energy_primary_date_of_birth = fields.Date(
        "Date of Birth", related="stage_2_dob", readonly=False
    )
    momentum_energy_primary_email = fields.Char(
        "Email", related="email_normalized", readonly=False
    )
    momentum_energy_primary_address_type = fields.Char("Address Type", default="POSTAL", readonly=True)
    momentum_energy_primary_street_number = fields.Char(
        "Street Number"
    )
    momentum_energy_primary_street_name = fields.Char(
        "Street Name"
    )
    momentum_energy_primary_unit_number = fields.Char("Unit Number")
    momentum_energy_primary_suburb = fields.Char("Suburb")
    momentum_energy_primary_state = fields.Selection(
        [
            ("NSW", "NSW"),
            ("VIC", "VIC"),
            ("QLD", "QLD"),
            ("WA", "WA"),
            ("SA", "SA"),
            ("TAS", "TAS"),
            ("ACT", "ACT"),
            ("NT", "NT"),
        ],
        string="State",
    )
    momentum_energy_primary_post_code = fields.Char("Post Code")
    momentum_energy_primary_phone_work = fields.Char(
        "Primary Work Phone"
    )
    momentum_energy_primary_phone_home = fields.Char(
        "Primary Home Phone"
    )
    momentum_energy_primary_phone_mobile = fields.Char(
        "Primary Mobile Phone"
    )
    momentum_energy_secondary_contact_type = fields.Char(
        "Secondary Contact Type", default="SECONDARY", readonly=True
    )
    momentum_energy_secondary_salutation = fields.Selection(
        [
            ("Mr.", "Mr."),
            ("Mrs.", "Mrs."),
            ("Ms.", "Ms."),
            ("Dr.", "Dr."),
            ("Prof.", "Prof."),
        ],
        string="Salutation",
    )
    momentum_energy_secondary_first_name = fields.Char("Secondary First Name")
    momentum_energy_secondary_middle_name = fields.Char("Secondary Middle Name")
    momentum_energy_secondary_last_name = fields.Char("Secondary Last Name")
    momentum_energy_secondary_country_of_birth = fields.Char(
        "Secondary Country of Birth"
    )
    momentum_energy_secondary_date_of_birth = fields.Date("Secondary Date of Birth")
    momentum_energy_secondary_email = fields.Char("Secondary Email")
    momentum_energy_secondary_address_type = fields.Char(
        "Secondary Address Type", default="POSTAL", readonly=True
    )
    momentum_energy_secondary_street_number = fields.Char("Secondary Street Number")
    momentum_energy_secondary_street_name = fields.Char("Secondary Street Name")
    momentum_energy_secondary_unit_number = fields.Char("Secondary Unit Number")
    momentum_energy_secondary_suburb = fields.Char("Secondary Suburb")
    momentum_energy_secondary_state = fields.Selection(
        [
            ("NSW", "NSW"),
            ("VIC", "VIC"),
            ("WA", "WA"),
            ("SA", "SA"),
            ("ACT", "ACT"),
            ("NT", "NT"),
        ],
        string="State",
    )
    momentum_energy_secondary_post_code = fields.Char("Secondary Post Code")
    momentum_energy_secondary_phone_work = fields.Char("Secondary Work Phone")
    momentum_energy_secondary_phone_home = fields.Char("Secondary Home Phone")
    momentum_energy_secondary_phone_mobile = fields.Char("Secondary Mobile Phone")
    momentum_energy_service_type = fields.Selection(
        [
            ("POWER", "Power"),
            ("GAS", "Gas"),
        ],
        string="Service Type",
    )
    momentum_energy_service_sub_type = fields.Selection(
        [
            ("TRANSFER", "Transfer"),
            ("MOVE IN", "Move In"),
            # ("NEW INSTALLATION", "New Installation")
        ],
        string="Service Sub Type",
    )
    momentum_energy_service_connection_id = fields.Char("Service Connection ID")
    momentum_energy_service_meter_id = fields.Char("Service Meter ID")
    momentum_energy_service_start_date = fields.Date("Service Start Date")
    momentum_energy_estimated_annual_kwhs = fields.Integer("Estimated Annual kWhs")
    momentum_energy_lot_number = fields.Char("Lot Number")
    momentum_energy_service_name = fields.Char("Service Name")
    momentum_energy_property_name = fields.Char("Property Name")
    momentum_energy_unit_type = fields.Selection(
        [
            ("APT", "APT"),
            ("CTGE", "CTGE"),
            ("DUP", "DUP"),
            ("F", "F"),
            ("FY", "FY"),
            ("HSE", "HSE"),
            ("KSK", "KSK"),
            ("MB", "MB"),
            ("MSNT", "MSNT"),
            ("OFF", "OFF"),
            ("PTHS", "PTHS"),
            ("RM", "RM"),
            ("SE", "SE"),
            ("SHED", "SHED"),
            ("SHOP", "SHOP"),
            ("SITE", "SITE"),
            ("SL", "SL"),
            ("STU", "STU"),
            ("TNCY", "TNCY"),
            ("TNHS", "TNHS"),
            ("U", "U"),
            ("VLLA", "VLLA"),
            ("WARD", "WARD"),
            ("WE", "WE"),
        ],
        string="Unit Type",
    )
    momentum_energy_unit_number = fields.Char(string="Unit Number")
    momentum_energy_floor_type = fields.Selection(
        [
            ("FLOOR", "Floor"),
            ("LEVEL", "Level"),
            ("GROUND", "Ground"),
        ],
        string="Floor Type",
    )
    momentum_energy_floor_number = fields.Char(string="Floor Number")
    momentum_energy_street_number_suffix = fields.Char("Street Number Suffix")
    momentum_energy_street_name_suffix = fields.Selection(
        [
            ("CN", "CN"),
            ("E", "E"),
            ("EX", "EX"),
            ("LR", "LR"),
            ("N", "N"),
            ("NE", "NE"),
            ("NW", "NW"),
            ("S", "S"),
            ("SE", "SE"),
            ("SW", "SW"),
            ("UP", "UP"),
            ("W", "W"),
        ],
        string="Street Name Suffix",
    )
    momentum_energy_service_street_number = fields.Char("Service Street Number")
    momentum_energy_service_street_name = fields.Char("Service Street Name")
    momentum_energy_service_street_type_code = fields.Selection(
        [
            ("ACCS", "ACCS"),("ACRE", "ACRE"),("ALLY", "ALLY"),
            ("ALWY", "ALWY"),("AMBL", "AMBL"),("ANCG", "ANCG"),
            ("APP", "APP"),("ARC", "ARC"),("ART", "ART"),
            ("ARTL", "ARTL"),("AVE", "AVE"),("BA", "BA"),
            ("BASN", "BASN"),("BAY", "BAY"),("BCH", "BCH"),
            ("BDGE", "BDGE"),("BDWY", "BDWY"),("BEND", "BEND"),
            ("BLK", "BLK"),("BOWL", "BOWL"),("BRAE", "BRAE"),
            ("BRAN", "BRAN"),("BRCE", "BRCE"),("BRET", "BRET"),
            ("BRK", "BRK"),("BROW", "BROW"),("BVD", "BVD"),
            ("BVDE", "BVDE"),("BWLK", "BWLK"),("BYPA", "BYPA"),
            ("CAUS", "CAUS"),("CCT", "CCT"),("CDS", "CDS"),
            ("CH", "CH"),("CIR", "CIR"),("CL", "CL"),
            ("CLDE", "CLDE"),("CLR", "CLR"),("CMMN", "CMMN"),
            ("CNN", "CNN"),("CNWY", "CNWY"),("CON", "CON"),
            ("COVE", "COVE"),("COWY", "COWY"),("CPS", "CPS"),
            ("CRCS", "CRCS"),("CRD", "CRD"),("CRES", "CRES"),
            ("CRF", "CRF"),("CRK", "CRK"),("CRSE", "CRSE"),
            ("CRSS", "CRSS"),("CRST", "CRST"),("CSO", "CSO"),
            ("CT", "CT"),("CTR", "CTR"),("CTTG", "CTTG"),
            ("CTYD", "CTYD"),("CUT", "CUT"),("DALE", "DALE"),
            ("DASH", "DASH"),("DELL", "DELL"),("DEVN", "DEVN"),
            ("DIP", "DIP"),("DIV", "DIV"),("DOCK", "DOCK"),
            ("DR", "DR"),("DRWY", "DRWY"),("DWNS", "DWNS"),
            ("EDGE", "EDGE"),("ELB", "ELB"),("END", "END"),
            ("ENT", "ENT"),("ESP", "ESP"),("EST", "EST"),
            ("EXP", "EXP"),("EXTN", "EXTN"),("FAWY", "FAWY"),
            ("FBRK", "FBRK"),("FITR", "FITR"),("FK", "FK"),
            ("FLTS", "FLTS"),("FOLW", "FOLW"),("FORD", "FORD"),
            ("FORM", "FORM"),("FRNT", "FRNT"),("FRTG", "FRTG"),
            ("FSHR", "FSHR"),("FTWY", "FTWY"),("FWY", "FWY"),
            ("GAP", "GAP"),("GATE", "GATE"),("GDN", "GDN"),
            ("GDNS", "GDNS"),("GLD", "GLD"),("GLEN", "GLEN"),
            ("GLY", "GLY"),("GR", "GR"),("GRA", "GRA"),
            ("GRN", "GRN"),("GRND", "GRND"),("GTE", "GTE"),
            ("GTES", "GTES"),("GTWY", "GTWY"),("HETH", "HETH"),
            ("HILL", "HILL"),("HLLW", "HLLW"),("HRBR", "HRBR"),
            ("HRD", "HRD"),("HTS", "HTS"),("HUB", "HUB"),
            ("HVN", "HVN"),("HWY", "HWY"),("INLT", "INLT"),
            ("INTG", "INTG"),("INTN", "INTN"),("ISLD", "ISLD"),
            ("JNC", "JNC"),("KEY", "KEY"),("KEYS", "KEYS"),
            ("LADR", "LADR"),("LANE", "LANE"),("LEDR", "LEDR"),
            ("LINE", "LINE"),("LINK", "LINK"),("LKT", "LKT"),
            ("LNWY", "LNWY"),("LOOP", "LOOP"),("LWR", "LWR"),
            ("MALL", "MALL"),("MANR", "MANR"),("MART", "MART"),
            ("MEAD", "MEAD"),("MEW", "MEW"),("MEWS", "MEWS"),
            ("MT", "MT"),("MWY", "MWY"),("NOOK", "NOOK"),
            ("NTH", "NTH"),("NULL", "NULL"),("OTLT", "OTLT"),
            ("OVAL", "OVAL"),("PARK", "PARK"),("PART", "PART"),
            ("PASS", "PASS"),("PATH", "PATH"),("PDE", "PDE"),
            ("PHWY", "PHWY"),("PKLD", "PKLD"),("PKT", "PKT"),
            ("PKWY", "PKWY"),("PL", "PL"),("PLAT", "PLAT"),
            ("PLM", "PLM"),("PLMS", "PLMS"),("PLZA", "PLZA"),
            ("PNT", "PNT"),("PORT", "PORT"),("PRDS", "PRDS"),
            ("PREC", "PREC"),("PROM", "PROM"),("PRST", "PRST"),
            ("PSGE", "PSGE"),("PSLA", "PSLA"),("QDRT", "QDRT"),
            ("QY", "QY"),("QYS", "QYS"),("RAMP", "RAMP"),
            ("RCH", "RCH"),("RD", "RD"),("RDGE", "RDGE"),
            ("RDS", "RDS"),("RDWY", "RDWY"),("REEF", "REEF"),
            ("RES", "RES"),("REST", "REST"),("RGWY", "RGWY"),
            ("RIDE", "RIDE"),("RING", "RING"),("RISE", "RISE"),
            ("RMBL", "RMBL"),("RND", "RND"),("RNDE", "RNDE"),
            ("RNGE", "RNGE"),("ROW", "ROW"),("ROWY", "ROWY"),
            ("RSNG", "RSNG"),("RTRN", "RTRN"),("RTT", "RTT"),
            ("RTY", "RTY"),("RUE", "RUE"),("RUN", "RUN"),
            ("RVR", "RVR"),("RVRA", "RVRA"),("SBWY", "SBWY"),
            ("SDNG", "SDNG"),("SHWY", "SHWY"),("SKLN", "SKLN"),
            ("SLPE", "SLPE"),("SND", "SND"),("SQ", "SQ"),
            ("ST", "ST"),("STPS", "STPS"),("STRA", "STRA"),
            ("STRP", "STRP"),("STRS", "STRS"),("STRT", "STRT"),
            ("SWY", "SWY"),("TARN", "TARN"),("TCE", "TCE"),
            ("THOR", "THOR"),("TMWY", "TMWY"),("TOP", "TOP"),
            ("TOR", "TOR"),("TRI", "TRI"),("TRK", "TRK"),
            ("TRLR", "TRLR"),("TUNL", "TUNL"),("TURN", "TURN"),
            ("TVSE", "TVSE"),("UPAS", "UPAS"),("UPR", "UPR"),
            ("VALE", "VALE"),("VDCT", "VDCT"),("VIEW", "VIEW"),
            ("VLGE", "VLGE"),("VLL", "VLL"),("VLLY", "VLLY"),
            ("VSTA", "VSTA"),("VUE", "VUE"),("VWS", "VWS"),
            ("WALK", "WALK"),
        ],
        string="Service Street Type Code",
    )


    momentum_energy_service_suburb = fields.Char("Service Suburb")
    momentum_energy_service_state = fields.Selection(
        [
            ("NSW", "NSW"),
            ("VIC", "VIC"),
            ("QLD", "QLD"),
            ("WA", "WA"),
            ("SA", "SA"),
            ("TAS", "TAS"),
            ("ACT", "ACT"),
            ("NT", "NT"),
        ],
        string="State",
    )
    momentum_energy_service_post_code = fields.Char("Service Post Code")
    momentum_energy_service_access_instructions = fields.Text(
        "Service Access Instructions"
    )
    momentum_energy_service_safety_instructions = fields.Selection(
        [
            ("NONE", "None"),
            ("CAUTION", "Caution"),
            ("DOG", "Dog"),
            ("ELECFENCE", "Electric Fence"),
            ("NOTKNOWN", "Not Known"),
            ("WORKSONSITE", "Works On Site"),
        ],
        string="Service Safety Instructions",
    )

    momentum_energy_offer_quote_date = fields.Datetime("Offer Quote Date")
    momentum_energy_service_offer_code = fields.Char("Rate ID")
    momentum_energy_owr = fields.Char("OWR")
    momentum_energy_service_plan_code = fields.Selection(
        [
            ("Bill Boss Electricity", "Bill Boss Electricity"),
            ("Suit Yourself Electricity", "Suit Yourself Electricity"),
            ("Suit Yourself Gas", "Suit Yourself Gas"),
            ("Strictly Business", "Strictly Business"),
            ("Warm Welcome", "Warm Welcome"),
            ("Warm Welcome Gas", "Warm Welcome Gas"),
            ("EV Does It", "EV Does It"),
        ],
        string="Service Plan Code",
    )

    momentum_energy_contract_term_code = fields.Selection(
        [
            ("OPEN", "Open"),
            ("12MTH", "12 Months"),
            ("24MTH", "24 Months"),
            ("36MTH", "36 Months"),
        ],
    )

    momentum_energy_contract_date = fields.Datetime("Contract Date")
    momentum_energy_payment_method = fields.Selection(
        [
            ("Cheque", "Cheque"),
            ("Direct Debit Via Bank Account", "Direct Debit Via Bank Account"),
            # ('bank_transfer', 'Bank Transfer')
        ],
        string="Payment Method",
    )
    momentum_energy_bill_cycle_code = fields.Selection(
        [
            ("Monthly", "Monthly"),
            ("Bi-Monthly", "Bi-Monthly"),
            ("Quarterly", "Quarterly"),
        ],
        string="Bill Cycle Code",
    )
    momentum_energy_bill_delivery_method = fields.Selection(
        [("EMAIL", "Email"), ("POST", "Post")],
        string="Bill Delivery Method",
    )
    momentum_energy_concession = fields.Boolean(
        string="Concession"
    )
    
    momentum_energy_concession_obtained = fields.Boolean(string="Concession Consent Obtained")
    momentum_energy_conc_has_ms = fields.Boolean(
        string="Whether the concession is for someone with MS(Multiple sclerosis)",
    )
    momentum_energy_conc_in_grp_home = fields.Boolean(
        string="Whether the concession is for group home"
    )
    momentum_energy_conc_start_date = fields.Date(
        string="Concession start date. (Must not be in future)."
    )
    momentum_energy_conc_end_date = fields.Date(
        string="Concession end date.(Must not be in Past)."
    )
    momentum_energy_conc_card_type_code = fields.Selection(
        [
            ("DVAGV", "DVAGV"),
            ("HCC", "HCC"),
            ("PCC", "PCC"),
            ("Pensioner Concession Card (PCC)", "Pensioner Concession Card (PCC)"),
            ("DVA Gold Card", "DVA Gold Card"),
            ("DVA Pension Concession Card", "DVA Pension Concession Card"),
            ("Health Care Card (HCC)", "Health Care Card (HCC)"),
            ("DVA TPI", "DVA TPI"),
            ("Disability Pension (EDA)", "Disability Pension (EDA)"),
            ("DVA War Widow/Widower", "DVA War Widow/Widower"),
            ("ImmiCard", "ImmiCard"),
            ("Tasmanian Concession Card", "Tasmanian Concession Card"),
            ("DVA PCC Only", "DVA PCC Only"),
            ("QLD Seniors Card", "QLD Seniors Card"),
            (
                "Low Income Health Care Card (LIHCC)",
                "Low Income Health Care Card (LIHCC)",
            ),
            ("LIHCC", "LIHCC"),
        ],
        string="Type of Concession Card",
        related="type_of_concession",
        readonly=False,
    )

    momentum_energy_conc_card_code = fields.Char(string="Concession card code.")
    momentum_energy_conc_card_number = fields.Char(string="Concession card number")
    momentum_energy_conc_card_exp_date = fields.Date(
        string="Concession card expiry date."
    )
    momentum_energy_card_first_name = fields.Char(
        string="First name of the contact person."
    )
    momentum_energy_card_last_name = fields.Char(
        string="Last name of the contact person."
    )
    momentum_transaction_id = fields.Char(string='Transaction ID')
    is_momentum_submitted = fields.Boolean(default=False)

    # AMEX CREDIT CARD FIELDS
    cc_prefix = fields.Selection(
        [
            ("n/a", "N/A"),
            ("mr", "Mr."),
            ("mrs", "Mrs."),
            ("ms", "Ms."),
            ("dr", "Dr."),
            ("miss", "Miss"),
        ],
        string="Prefix",
    )
    cc_customer_name = fields.Char(
        "Customer Name", related="contact_name", readonly=False
    )
    cc_first_name = fields.Char("First Name", related="contact_name", readonly=False)
    cc_last_name = fields.Char("Last Name", related="contact_name", readonly=False)
    cc_job_title = fields.Char("Job Title")
    cc_phone = fields.Char("Phone", related="phone", readonly=False)
    cc_email = fields.Char("Email", related="email_normalized", readonly=False)
    cc_address = fields.Char("Enter postcode or address")
    cc_run_business = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Do you run a business?"
    )
    cc_active_abn = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Do you have active ABN?"
    )
    cc_annual_revenue = fields.Selection(
        [
            ("under_2m", "Under ~ $2M"),
            ("2m_10m", "$2M ~ $10M"),
            ("10m_50m", "$10M ~ $50M"),
            ("50m_100m", "$50M ~ $100M"),
            ("100m_above", "Above $100M"),
        ],
        string="Annual Company Revenue",
    )
    cc_annual_spend = fields.Selection(
        [
            ("under_1m", "Under ~ $1M"),
            ("2m_5m", "$2M ~ $5M"),
            ("6m_10m", "$6M ~ $10M"),
            ("11m_15m", "$11M ~ $15M"),
            ("16m_20m", "$16M ~ $20M"),
            ("20m_above", "Above $20M"),
        ],
        string="Annual Spend",
    )
    cc_existing_products = fields.Char("Existing Competitor Products")
    cc_expense_tools = fields.Char("Expense Management Tools")
    cc_additional_info = fields.Text("Additional information for sales team")
    cc_consent_personal_info = fields.Boolean(
        string="I have obtained the express consent of the above individual to provide their personal information as noted above to American Express for purposes of offering American Express Commercial Payment Products to the business of the individual."
    )
    cc_consent_contact_method = fields.Selection(
        [("phone", "Phone"), ("email", "Email")],
        string="I have obtained the consent of above companies to contact the appointed representative via",
    )

    cc_contact_preference = fields.Selection(
        [("me_first", "Me first"), ("referred_first", "The referred contact first")],
        string="In order to best process this lead the salesperson should contact",
    )
    cc_stage2_business = fields.Char("Business Name")
    cc_stage2_business_address = fields.Char("Business Address")
    cc_stage2_email = fields.Char("Email", related="email_normalized", readonly=False)
    cc_stage2_monthly = fields.Char("Estimated Monthly Spend")
    cc_stage2_annual = fields.Char("Estimated Annual Turnover")
    cc_stage2_running = fields.Char("How long does the business running")
    cc_stage2_existing = fields.Char("Any existing business credit card")
    cc_stage2_abn = fields.Char("ABN")
    cc_stage2_tool = fields.Char("Expense Tool")
    cc_stage2_dnc = fields.Char("DNC")
    cc_stage2_agent = fields.Char("Agent Name")
    cc_stage2_closer = fields.Char("Closer Name")
    # CREDIT CARD - AMEX FIELDS
    amex_date = fields.Date(string="Date")
    amex_center = fields.Char(string="Center", default="Utility Hub")
    amex_company_name = fields.Char(string="Company Name")
    amex_abn = fields.Char(string="ABN", related="cc_stage2_abn", readonly=False)
    amex_address_1 = fields.Char(string="Address Line 1")
    amex_address_2 = fields.Char(string="Address Line 2")
    amex_suburb = fields.Char(string="Suburb")
    amex_state = fields.Char(string="State")
    amex_country = fields.Char(string="Country")
    amex_business_website = fields.Char(string="Website")
    amex_saluation = fields.Selection(
        [
            ("n/a", "N/A"),
            ("mr", "Mr."),
            ("mrs", "Mrs."),
            ("ms", "Ms."),
            ("dr", "Dr."),
            ("miss", "Miss"),
        ],
        string="Prefix",
        default="mr",
    )
    amex_first_name = fields.Char(
        string="First Name", related="contact_name", readonly=False
    )
    amex_last_name = fields.Char(string="Last Name")
    amex_position = fields.Char(string="Position in Business")
    amex_contact = fields.Char(string="Contact Number", related="phone", readonly=False)
    amex_email = fields.Char(string="Email", related="email_normalized", readonly=False)
    amex_current_turnover = fields.Char(
        string="Current turnover less than 2 million or more"
    )
    amex_estimated_expense = fields.Char(string="Estimated Expenses On Card")
    amex_existing_product = fields.Char(string="Existing Competitor Product")
    amex_additional_info = fields.Char(string="Additional Information for Sales Team")
    amex_tool_used = fields.Char(string="Expense Management Tool Used")

    # BROADBAND NBN FIELDS
    in_current_address = fields.Char(string="Enter your postcode or address")
    in_important_feature = fields.Selection(
        [
            ("speed", "Speed"),
            ("price", "Price"),
            ("reliability", "Reliability"),
        ],
        string="What is the most important feature to you?",
    )
    in_speed_preference = fields.Selection(
        [
            ("25Mb", "25 Mbps"),
            ("50Mb", "50 Mbps"),
            ("100Mb", "100 Mbps"),
            ("not_sure", "Not Sure"),
        ],
        string="Do you have a speed preferece?",
    )
    in_broadband_reason = fields.Selection(
        [
            ("moving", "I am Moving"),
            ("better_plan", "I want a better plan"),
            ("connection", "I need broadband connected"),
        ],
        string="Why are you looking into broadband options?",
    )
    in_when_to_connect_type = fields.Selection(
        [
            ("asap", "ASAP"),
            ("dont_mind", "I don't mind"),
            ("specific_date", "Choose a date"),
        ],
        string="When would you like broadband connected?",
    )
    in_when_to_connect_date = fields.Date(string="Select connection date?")
    in_current_provider = fields.Char("Current Provider Name")
    in_current_plan = fields.Char("Current Plan Name")
    in_current_price = fields.Char("Current Plan Price Per Month")
    in_internet_users_count = fields.Selection(
        [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5+", "5+"),
        ],
        string="How many people are using the internet?",
    )
    in_internet_usage_type = fields.Selection(
        [
            ("browsing_email", "Browsing and Email"),
            ("work", "Work and Study"),
            ("social_media", "Social Media"),
            ("gaming", "Online Gaming"),
            ("streaming", "Streaming video/TV/Movies"),
        ],
        string="How will you use the internet?",
    )
    in_compare_plans = fields.Selection(
        [("no", "No"), ("yes", "Yes")],
        string="Would you also like to comapre your energy plans to see if you could save?",
    )
    in_name = fields.Char(
        string="Customer Name", related="contact_name", readonly=False
    )
    in_contact_number = fields.Char(
        string="Mobile Number", related="phone", readonly=False
    )
    in_contact_number_alt = fields.Char(string="Alt. Mobile Number")
    in_email = fields.Char(string="Email", related="email_normalized", readonly=False)
    in_supply_address = fields.Char("Supply Address")
    in_customer_dob = fields.Date("Date of Birth")
    in_lead_agent = fields.Char("Lead Agent Name")
    in_request_callback = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Request Callback"
    )
    in_accept_terms = fields.Boolean(
        string="By submitting your details you agree that you have read and agreed to the Terms and Conditions and Privacy Policy."
    )
    in_stage2_provider = fields.Selection(
        [("optus", "Optus NBN"), ("dodo", "DODO NBN"), ("iprimus", "IPRIMUS")],
        string="Provider Name",
    )
    in_stage2_plan = fields.Char("Plan name offered")
    in_stage2_price = fields.Char("Plan price per month offered")
    in_stage2_dnc = fields.Char("DNC")
    in_stage2_agent = fields.Char("Lead Agenet Name")
    in_stage2_closer = fields.Char("Closer Name")
    in_stage2_date = fields.Date("Date of Sale")
    in_stage2_ref = fields.Char("Sales Reference No")
    in_stage2_avc = fields.Char("AVC ID")

    # DODO NBN SALES FORM FILEDS

    do_nbn_receipt = fields.Char("DODO Receipt Number")
    do_nbn_service = fields.Char("Service Type")
    do_nbn_service = fields.Char("Service Type")
    do_nbn_plans = fields.Selection(
        [("$79.99/250MBPS", "$79.99/250 MBPS"), ("superfast", "HOME SUPERFAST")],
        string="Plan with DODO",
    )
    do_nbn_current = fields.Char("Current Provider")
    do_nbn_current_no = fields.Char("Current Provider Account No")
    do_nbn_title = fields.Selection(
        [
            ("n/a", "N/A"),
            ("mr", "Mr."),
            ("mrs", "Mrs."),
            ("ms", "Ms."),
            ("dr", "Dr."),
            ("miss", "Miss"),
        ],
        string="Title",
        default="mr",
    )
    do_first_name = fields.Char(
        string="First Name", related="contact_name", readonly=False
    )
    do_last_name = fields.Char(string="Last Name")
    do_mobile_no = fields.Char(string="Mobile No", related="phone", readonly=False)
    do_installation_address = fields.Char(
        string="Installation address - Unit/Flat Number"
    )
    do_house_number = fields.Char(string="House No")
    do_street_name = fields.Char(string="Street Name")
    do_street_type = fields.Char(string="Street Type")
    do_suburb = fields.Char(string="Installation address-Suburb")
    do_state = fields.Char(string="State")
    do_post_code = fields.Char("Post Code")
    do_sale_date = fields.Date(string="Sale Date")
    do_center_name = fields.Char(string="Center Name", default="Utility Hub")
    do_closer_name = fields.Char(string="Closer Name")
    do_dnc_ref_no = fields.Char(string="DNC Reference No")
    do_dnc_exp_date = fields.Date(string="DNC Expiry Date")
    do_audit_1 = fields.Char(string="Audit 1")
    do_audit_2 = fields.Char(string="Audit 2")
    # OPTUS NBN FORM FIELDS
    optus_date = fields.Date(string="Sale Date")
    optus_activation = fields.Date(string="Activation Date")
    optus_order = fields.Char(string="Order Number")
    optus_customer = fields.Char(
        string="Customer Name", related="contact_name", readonly=False
    )
    optus_address = fields.Char(string="Service Address", related="in_supply_address", readonly=False)
    optus_service = fields.Char(
        string="Service"
    )
    optus_plan = fields.Char(string="Plan")
    optus_per_month = fields.Char(string="Cost Per Month")
    optus_center = fields.Char(string="Center", default="Utility Hub")
    optus_salesperson = fields.Char(string="Sales Person")
    optus_contact = fields.Char(
        string="Contact Number", related="phone", readonly=False
    )
    optus_email = fields.Char(
        string="Email", related="email_normalized", readonly=False
    )
    optus_notes = fields.Char(string="Notes")
    optus_dcn = fields.Char(string="DCN Reference")
    optus_audit_1 = fields.Char(string="Audit 1")
    optus_audit_2 = fields.Char(string="Audit 2")

    # HOME MOVING FORM FIELDS
    hm_moving_date = fields.Date("Moving Date")
    hm_address = fields.Char("Address")
    hm_property_type = fields.Selection(
        [
            ("business", "Business"),
            ("residential", "Residential"),
        ],
        string="What type of propery",
    )
    hm_ownership = fields.Selection(
        [
            ("own", "Own"),
            ("rent", "Rent"),
        ],
        string="Property Ownership",
    )
    hm_status = fields.Selection(
        [
            ("n/a", "N/A"),
            ("dr", "Dr."),
            ("mr", "Mr."),
            ("mrs", "Mrs."),
            ("ms", "Ms."),
            ("miss", "Miss."),
        ],
        string="Status",
    )
    hm_first_name = fields.Char("First Name")
    hm_last_name = fields.Char("Last Name")
    hm_job_title = fields.Char("Job Title")
    hm_dob = fields.Date("Date of Birth")
    hm_friend_code = fields.Char("Refer a Friend Code")
    hm_mobile = fields.Char("Mobile")
    hm_work_phone = fields.Char("Work Phone")
    hm_home_phone = fields.Char("Home Phone")

    hm_email = fields.Char("Email")
    hm_how_heard = fields.Selection(
        [
            ("google", "Google"),
            ("facebook", "Facebook"),
            ("word_of_mouth", "Word of Mouth"),
            ("real_estate", "Real Estate"),
            ("other", "Other"),
        ],
        string="How did you hear about us?",
    )
    hm_agency_name = fields.Char("Real estate agency name")
    hm_broker_name = fields.Char("Broker name")
    hm_agency_contact_number = fields.Char("Real estate contact number")
    hm_connect_electricity = fields.Boolean("Electricity")
    hm_connect_gas = fields.Boolean("Gas")
    hm_connect_internet = fields.Boolean("Internet")
    hm_connect_water = fields.Boolean("Water")
    hm_connect_tv = fields.Boolean("Pay TV")
    hm_connect_removalist = fields.Boolean("Removalist")
    hm_accept_terms = fields.Boolean("I accept the Terms and Conditions")
    hm_recaptcha_checked = fields.Boolean("I'm not a robot")

    # BUSINESS LOAN FORM FIELDS
    bs_amount_to_borrow = fields.Selection([
        ("under_50k","Under $50k"),
        ("50k_100k","$50k - $100k"),
        ("100k_150k","$100k - $150k"),
        ("200k_300k","$200k - $300k"),
        ("300k_500k","$300k - $500k"),
        ("above_500k","Above $500k"),

    ],string="How much would you like to borrow?")
    bs_business_name = fields.Char(string="Name of your business")
    bs_trading_duration = fields.Selection(
        [
            ("0-6 months", "0-6 Months"),
            ("6-12 months", "6-12 Months"),
            ("12-24 months", "12-24 Months"),
            ("over 24 months", "Over 24 Months"),
        ],
        string="How long have you been trading",
    )
    bs_monthly_turnover = fields.Char(string="What is your monthly turnover")
    bs_first_name = fields.Char(string="First Name")
    bs_last_name = fields.Char(string="Last Name")
    bs_email = fields.Char(string="Email")
    bs_home_owner = fields.Boolean(string="Are you a home owner?")
    bs_accept_terms = fields.Boolean(string="Accept terms and conditions")

    # HOME LOAN FIELDS
    hl_user_want_to = fields.Selection(
        [
            ("refinance", "I want to refinance"),
            ("buy home", "I want to buy a home"),
        ],
        string="What would you like to do?",
    )
    hl_expected_price = fields.Integer(string="What is your exptected price?")
    hl_deposit_amount = fields.Integer(string="How much deposit do you have?")
    hl_buying_reason = fields.Selection(
        [
            ("just_exploring", "Just exploring options"),
            ("planning_to_buy", "Planning to buy home in next 6 months"),
            ("actively_looking", "Actively looking/made an offer"),
            ("exchanged_contracts", "Exchanged Contracts"),
        ],
        string="What best describes your home buying situation?",
    )
    hl_first_home_buyer = fields.Boolean(string="Are you a first home buyer")
    hl_property_type = fields.Selection(
        [
            ("established_home", "Established Home"),
            ("newly_built", "Newly built/off the plan"),
            ("vacant_land", "Vacant land to build on"),
        ],
        string="What kind of property are you looking for?",
    )
    hl_property_usage = fields.Selection(
        [
            ("to_live", "I will live there"),
            ("for_investment", "It is for investment purposes"),
        ],
        string="How will this property be used?",
    )
    hl_credit_history = fields.Selection(
        [
            ("excellent", "Excellent - no issues"),
            ("average", "Average paid default"),
            ("fair", "Fair"),
            ("don't know", "I don't know"),
        ],
        string="What do you think your credit history is?",
    )
    hl_income_source = fields.Selection(
        [
            ("employee", "I am an employee"),
            ("business", "I have my own business"),
            ("other", "Other"),
        ],
        string="How do you earn your income?",
    )
    hl_first_name = fields.Char(string="First Name")
    hl_last_name = fields.Char(string="Last Name")
    hl_contact = fields.Char(string="Contact Number")
    hl_email = fields.Char(string="Email")
    hl_accept_terms = fields.Boolean(string="Agree to accept terms and conditions")

    # HEALTH INSURANCE FIELDS
    hi_current_address = fields.Char(string="Current address")
    hi_cover_type = fields.Selection(
        [
            ("hospital_extras", "Hospital + Extras"),
            ("hospital", "Hospital only"),
            ("extras", "Extras only"),
        ],
        string="Select type of cover",
    )
    hi_have_insurance_cover = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Do you have health inssurance cover"
    )
    hi_insurance_considerations = fields.Selection(
        [
            ("health_concern", "I have a specific health concern"),
            ("save_money", "I am looking to save money on my health premium"),
            ("no_insurance_before", "I haven't held health insurance before"),
            ("better_health_cover", "I am looking for better health cover"),
            ("need_for_tax", "I need it for my tax"),
            ("planning_a_baby", "I am planning a baby"),
            ("changed_circumstances", "My circumstances have changed"),
            ("compare_options", "I just want to compare options"),
        ],
        string="What are your main considerations when looking for a new health insurance cover?",
    )
    hi_dob = fields.Date(string="What is your date of birth")
    hi_annual_taxable_income = fields.Selection(
        [
            ("$97,000_or_less", "$97,000 or less (Base Tier)"),
            ("$97,001_$113,000", "$97,001 - $113,000 (Tier 1)"),
            ("$113,001_$151,000", "$113,001 - $151,000 (Tier 2)"),
            ("$151,001_or_more", "$151,001 or more (Tier 3)"),
        ],
        string="What is your annual taxable income?",
    )
    hi_full_name = fields.Char(string="Full Name")
    hi_contact_number = fields.Char(string="Contact Number")
    hi_email = fields.Char(string="Email")

    # VEU FIEDLS
    u_first_name = fields.Char(string="First Name")
    u_last_name = fields.Char(string="Last Name")
    u_mobile_no = fields.Char(string="Mobile No")
    u_email = fields.Char(string="Email")
    u_post_code = fields.Char("Post Code")
    u_interested_in = fields.Selection(
        [
            ("air", "Air Conitioning Rebate"),
            ("water_res", "Hot Water System (Residential)"),
            ("water_com", "Hot Water System (Commercial)"),
        ],
        string="Rebate Interested In",
        default="air",
    )
    u_how = fields.Char(string="How did you hear about us")
    u_accept_terms = fields.Boolean(
        string="By submitting your details you agree that you have read and agreed to the terms and conditions and privacy policy",
        default=False,
    )



    @api.model_create_multi
    def create(self, vals_list):
        """On create, use default stage and compute lead_stage"""
        _logger.info("Creating new leads: %s", vals_list)
        leads = super().create(vals_list)

        return leads

    def action_save_and_close(self):
        """Save record and close the form view"""
        self.ensure_one()
        _logger.info("Save & Close called for lead ID: %s", self.id)

        # Execute stage logic and get optional message
        qa_message = self._handle_stage_logic()

        # Notify the UI and close the form
        messages = []
        if qa_message:
            messages.append(qa_message)
        messages.append("Lead saved successfully.")

        return {
            "type": "ir.actions.client",
            "tag": "close_lead_form",
            "params": {
                "title": "Lead Update",
                "messages": messages,
            },
        }

    def _handle_stage_logic(self):
        Stage = self.env["crm.stage"]

        # Pre-cache stages
        stages_cache = {}
        stage_definitions = [
            ("Won", 12),
            ("On Hold", 13),
            ("Failed", 14),
            ("Call Back", 11),
            ("Lost", 6),
            ("Sold-Pending Quality", 8),
            ("Lead Assigned", 5),
            ("Sale Closed", 15),
            ("Sale QA Hold", 16),
            ("Sale QA Failed", 17),
        ]
        for name, sequence in stage_definitions:
            stage = Stage.search([("name", "=", name)], limit=1)
            if not stage:
                stage = Stage.create({"name": name, "sequence": sequence})
            stages_cache[name] = stage

        lead = self
        vals_to_write = {}
        qa_message = None

        if lead.lead_stage == "4":
            if (
                lead.stage_3_dispostion == "closed"
                and lead.lead_for in ("energy_website", "energy_call_center")
                and lead.stage_2_campign_name == "momentum"
            ):
                lead._send_momentum_energy()

            if lead.stage_3_dispostion == "closed":
                vals_to_write["stage_id"] = stages_cache["Sale Closed"].id
            elif lead.stage_3_dispostion == "on_hold":
                vals_to_write["stage_id"] = stages_cache["Sale QA Hold"].id
            elif lead.stage_3_dispostion == "failed":
                vals_to_write["stage_id"] = stages_cache["Sale QA Failed"].id

        # Stage 3 → Stage 4

        elif lead.lead_stage == "3":
            if lead.stage_3_dispostion == "closed":
                vals_to_write["stage_id"] = stages_cache["Sale Closed"].id
                vals_to_write["lead_stage"] = "4"
            elif lead.stage_3_dispostion == "on_hold":
                vals_to_write["stage_id"] = stages_cache["Sale QA Hold"].id
            elif lead.stage_3_dispostion == "failed":
                vals_to_write["stage_id"] = stages_cache["Sale QA Failed"].id

        elif lead.lead_stage == "2":
            if lead.disposition == "callback":
                vals_to_write["stage_id"] = stages_cache["Call Back"].id
            elif lead.disposition == "lost":
                vals_to_write["stage_id"] = stages_cache["Lost"].id
            elif lead.disposition == "sold_pending_quality":
                vals_to_write["stage_id"] = stages_cache["Sold-Pending Quality"].id
                vals_to_write["lead_stage"] = "3"
                qa_message = "✅ Lead has been transferred for QA Audit."

        elif lead.lead_stage == "1":
            if (
                lead.en_name
                or lead.en_contact_number
                or lead.cc_prefix
                or lead.cc_customer_name
                or lead.in_name
                or lead.in_contact_number
            ):
                vals_to_write["lead_stage"] = "2"
                vals_to_write["stage_id"] = stages_cache["Lead Assigned"].id

        if vals_to_write:
            lead.with_context(skip_stage_assign=True).write(vals_to_write)

        return qa_message

    # OLD WORKING CODE

    # def action_save_and_close(self):
    #     """Save record and close the form view"""
    #     self.ensure_one()
    #     _logger.info("Save & Close called for lead ID: %s", self.id)

    #     # Execute your stage logic
    #     self._handle_stage_logic()

    #     # Notify the UI and close the form
    #     return {
    #         "type": "ir.actions.client",
    #         "tag": "close_lead_form",
    #         "params": {
    #             "title": "Lead Saved ✅",
    #             "message": "Lead saved successfully. Closing form...",

    #         },
    #     }

    # def _handle_stage_logic(self):
    #     """
    #     Extracted from your write() to avoid recursion and handle
    #     all stage transitions in one place.
    #     """
    #     Stage = self.env["crm.stage"]

    #     # Pre-cache stages
    #     stages_cache = {}
    #     stage_definitions = [
    #         ("Won", 12),
    #         ("On Hold", 13),
    #         ("Failed", 14),
    #         ("Call Back", 11),
    #         ("Lost", 6),
    #         ("Sold-Pending Quality", 8),
    #         ("Lead Assigned", 5),
    #         ("Sale Closed", 15),
    #         ("Sale QA Hold", 16),
    #         ("Sale QA Failed", 17)
    #     ]

    #     for name, sequence in stage_definitions:
    #         stage = Stage.search([("name", "=", name)], limit=1)
    #         if not stage:
    #             stage = Stage.create({"name": name, "sequence": sequence})
    #         stages_cache[name] = stage

    #     # Process the logic for this lead
    #     lead = self
    #     vals_to_write = {}

    #     if lead.lead_stage == "3":
    #         if lead.stage_3_dispostion == "closed" and lead.lead_for == "energy" and lead.stage_2_campign_name == "momentum":
    #             lead._send_momentum_energy()

    #         if lead.stage_3_dispostion == "closed":
    #             vals_to_write["stage_id"] = stages_cache["Sale Closed"].id
    #         elif lead.stage_3_dispostion == "on_hold":
    #             vals_to_write["stage_id"] = stages_cache["Sale QA Hold"].id
    #         elif lead.stage_3_dispostion == "failed":
    #             vals_to_write["stage_id"] = stages_cache["Sale QA Failed"].id

    #     elif lead.lead_stage == "2":
    #         if lead.disposition == "callback":
    #             vals_to_write["stage_id"] = stages_cache["Call Back"].id
    #         elif lead.disposition == "lost":
    #             vals_to_write["stage_id"] = stages_cache["Lost"].id
    #         elif lead.disposition == "sold_pending_quality":
    #             vals_to_write["stage_id"] = stages_cache["Sold-Pending Quality"].id
    #             vals_to_write["lead_stage"] = "3"

    #     elif lead.lead_stage == "1":
    #         if lead.en_name or lead.en_contact_number or lead.cc_prefix or lead.cc_first_name or lead.in_current_address:
    #             vals_to_write["lead_stage"] = "2"
    #             vals_to_write["stage_id"] = stages_cache["Lead Assigned"].id

    #     if vals_to_write:
    #         lead.with_context(skip_stage_assign=True).write(vals_to_write)

    # def write(self, vals):
    #     """Override write to handle stage assignment after field updates"""
    #     _logger.info("Updating lead %s with values: %s", self.ids, vals)

    #     res = super().write(vals)

    #     # Skip stage assignment if context flag is set
    #     if self.env.context.get("skip_stage_assign"):
    #         return res

    #     Stage = self.env["crm.stage"]

    #     # Pre-fetch or create all possible stages ONCE before the loop
    #     stages_cache = {}
    #     stage_definitions = [
    #         ("Won", 12),
    #         ("On Hold", 13),
    #         ("Failed", 14),
    #         ("Call Back", 11),
    #         ("Lost", 6),
    #         ("Sold-Pending Quality", 8),
    #         ("Lead Assigned", 5),
    #         ("Sale Closed", 15),
    #         ("Sale QA Hold", 16),
    #         ("Sale QA Failed", 17)
    #     ]

    #     for stage_name, sequence in stage_definitions:
    #         stage = Stage.search([("name", "=", stage_name)], limit=1)
    #         if not stage:
    #             stage = Stage.create({"name": stage_name, "sequence": sequence})
    #         stages_cache[stage_name] = stage

    #     # Process each lead
    #     for lead in self:
    #         _logger.info("Processing lead: %s, lead_for: %s", lead.id, lead.lead_for)

    #         new_stage = None

    #         # STAGE 3 DISPOSITIONS
    #         if lead.lead_stage == "3":
    #             if lead.stage_3_dispostion == "closed" and lead.lead_for == "energy" and lead.stage_2_campign_name == "momentum":
    #                 lead._send_momentum_energy()

    #             if lead.stage_3_dispostion == "closed":
    #                 new_stage = stages_cache["Sale Closed"]
    #                 _logger.info("Lead %s - Moving to Won stage", lead.id)
    #             elif lead.stage_3_dispostion == "on_hold":
    #                 new_stage = stages_cache["Sale QA Hold"]
    #                 _logger.info("Lead %s - Moving to On Hold stage", lead.id)
    #             elif lead.stage_3_dispostion == "failed":
    #                 new_stage = stages_cache["Sale QA Failed"]
    #                 _logger.info("Lead %s - Moving to Failed stage", lead.id)

    #         # STAGE 2 DISPOSITIONS
    #         elif lead.lead_stage == "2":
    #             if lead.disposition == "callback":
    #                 new_stage = stages_cache["Call Back"]
    #                 _logger.info("Lead %s - Moving to Call Back stage", lead.id)
    #             elif lead.disposition == "lost":
    #                 new_stage = stages_cache["Lost"]
    #                 _logger.info("Lead %s - Moving to Lost stage", lead.id)
    #             elif lead.disposition == "sold_pending_quality":
    #                 new_stage = stages_cache["Sold-Pending Quality"]
    #                 lead.with_context(skip_stage_assign=True).write({"lead_stage":"3"})
    #                 _logger.info("Lead %s - Moving to Sold-Pending Quality stage", lead.id)

    #         elif lead.lead_stage == "1":
    #             if lead.en_name or lead.en_contact_number or lead.cc_prefix or lead.cc_first_name or lead.in_current_address:
    #                 lead.with_context(skip_stage_assign=True).write({"lead_stage":"2"})
    #                 new_stage = stages_cache["Lead Assigned"]

    #         # Apply stage update if needed
    #         if new_stage:
    #             if lead.stage_id.id != new_stage.id:
    #                 _logger.info("Applying stage update for lead %s: %s -> %s",
    #                         lead.id, lead.stage_id.name, new_stage.name)
    #                 # Use SQL update to avoid recursion
    #                 self.env.cr.execute(
    #                     "UPDATE crm_lead SET stage_id = %s WHERE id = %s",
    #                     (new_stage.id, lead.id)
    #                 )
    #                 # Invalidate cache to ensure fresh data
    #                 lead.invalidate_recordset(['stage_id'])
    #         else:
    #             # Run normal stage assignment for other cases
    #             _logger.info("Running normal stage assignment for lead %s", lead.id)
    #             lead._assign_lead_assigned_stage()

    #     return res

    def _assign_lead_assigned_stage(self):
        """Move to 'Lead Assigned' CRM stage when Stage 1 is complete."""
        Stage = self.env["crm.stage"]

        for lead in self:

            if lead.lead_stage == "1" and lead.en_name or lead.en_contact_number:
                # Find or create "Lead Assigned" stage
                stage = Stage.search([("name", "=", "Lead Assigned")], limit=1)
                _logger.info("Stage EXISTS..............")
                if not stage:
                    _logger.info("Creating new 'Lead Assigned' stage")
                    stage = Stage.create(
                        {
                            "name": "Lead Assigned",
                            "sequence": 5,
                        }
                    )

                if lead.stage_id.id != stage.id:
                    _logger.info("Assigning lead %s to 'Lead Assigned' stage", lead.id)
                    lead.with_context(skip_stage_assign=True).write(
                        {"stage_id": stage.id}
                    )
                else:
                    _logger.info("Lead %s already in 'Lead Assigned' stage", lead.id)
            else:
                # Assign default CRM stage if none set and still in stage 1
                if not lead.stage_id:
                    default_stage = Stage.search([], order="sequence ASC", limit=1)
                    if default_stage:
                        _logger.info(
                            "Assigning lead %s to default stage: %s",
                            lead.id,
                            default_stage.name,
                        )
                        lead.with_context(skip_stage_assign=True).write(
                            {"stage_id": default_stage.id}
                        )

    def _send_momentum_energy(self):
        """Prepare payload and POST to Momentum endpoint, then log response."""
        self.ensure_one()

        # -------------------------------
        # Transaction block
        # -------------------------------
        transaction = {
            "transactionReference": self.momentum_energy_transaction_reference,
            "transactionChannel": self.momentum_energy_transaction_channel,
            "transactionDate": (
                self.momentum_energy_transaction_date.replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
                if self.momentum_energy_transaction_date
                else None
            ),
            "transactionVerificationCode": self.momentum_energy_transaction_verification_code,
            "transactionSource": self.momentum_energy_transaction_source,
        }

        # -------------------------------
        # Contacts block
        # -------------------------------
        contacts = {
            "primaryContact": {
                "contactType": self.momentum_energy_primary_contact_type,
                "salutation": self.momentum_energy_primary_salutation,
                "firstName": self.momentum_energy_primary_first_name,
                # "middleName": self.momentum_energy_primary_middle_name,
                "lastName": self.momentum_energy_primary_last_name,
                "countryOfBirth": self.momentum_energy_primary_country_of_birth,
                "dateOfBirth": (
                    self.momentum_energy_primary_date_of_birth.isoformat()
                    if self.momentum_energy_primary_date_of_birth
                    else None
                ),
                "email": self.momentum_energy_primary_email,
                "addresses": [
                    {
                        "addressType": self.momentum_energy_primary_address_type,
                        "streetNumber": self.momentum_energy_primary_street_number,
                        "streetName": self.momentum_energy_primary_street_name,
                        "unitNumber": self.momentum_energy_primary_unit_number,
                        "suburb": self.momentum_energy_primary_suburb,
                        "state": self.momentum_energy_primary_state,
                        "postCode": self.momentum_energy_primary_post_code,
                    }
                ],
            },
        }

        if (self.momentum_energy_primary_middle_name):
            contacts["primaryContact"]["middleName"] = self.momentum_energy_primary_middle_name

        # 🧩 Dynamically include only non-empty phone numbers for primary contact
        primary_phones = []
        if self.momentum_energy_primary_phone_work:
            primary_phones.append({"contactPhoneType": "WORK", "phone": self.momentum_energy_primary_phone_work})
        if self.momentum_energy_primary_phone_home:
            primary_phones.append({"contactPhoneType": "HOME", "phone": self.momentum_energy_primary_phone_home})
        if self.momentum_energy_primary_phone_mobile:
            primary_phones.append({"contactPhoneType": "MOBILE", "phone": self.momentum_energy_primary_phone_mobile})

        if primary_phones:
            contacts["primaryContact"]["contactPhones"] = primary_phones


        # 🧠 Build secondary contact only if it has data
        secondary_fields = [
            self.momentum_energy_secondary_first_name,
            self.momentum_energy_secondary_last_name,
            self.momentum_energy_secondary_email,
            self.momentum_energy_secondary_phone_mobile,
            self.momentum_energy_secondary_phone_home,
            self.momentum_energy_secondary_phone_work,
            self.momentum_energy_secondary_street_number,
            self.momentum_energy_secondary_street_name,
            self.momentum_energy_secondary_suburb,
            self.momentum_energy_secondary_state,
            self.momentum_energy_secondary_post_code,
        ]

        # ✅ Only include secondary contact if at least one field has value
        if any(secondary_fields):
            contacts["secondaryContact"] = {
                "contactType": self.momentum_energy_secondary_contact_type,
                "salutation": self.momentum_energy_secondary_salutation,
                "firstName": self.momentum_energy_secondary_first_name,
                "middleName": self.momentum_energy_secondary_middle_name,
                "lastName": self.momentum_energy_secondary_last_name,
                "countryOfBirth": self.momentum_energy_secondary_country_of_birth,
                "dateOfBirth": (
                    self.momentum_energy_secondary_date_of_birth.isoformat()
                    if self.momentum_energy_secondary_date_of_birth
                    else None
                ),
                "email": self.momentum_energy_secondary_email,
                "addresses": [
                    {
                        "addressType": self.momentum_energy_secondary_address_type,
                        "streetNumber": self.momentum_energy_secondary_street_number,
                        "streetName": self.momentum_energy_secondary_street_name,
                        "unitNumber": self.momentum_energy_secondary_unit_number,
                        "suburb": self.momentum_energy_secondary_suburb,
                        "state": self.momentum_energy_secondary_state,
                        "postCode": self.momentum_energy_secondary_post_code,
                    }
                ],
            }

            # 📞 Add only non-empty phones for secondary contact
            secondary_phones = []
            if self.momentum_energy_secondary_phone_work:
                secondary_phones.append({"contactPhoneType": "WORK", "phone": self.momentum_energy_secondary_phone_work})
            if self.momentum_energy_secondary_phone_home:
                secondary_phones.append({"contactPhoneType": "HOME", "phone": self.momentum_energy_secondary_phone_home})
            if self.momentum_energy_secondary_phone_mobile:
                secondary_phones.append({"contactPhoneType": "MOBILE", "phone": self.momentum_energy_secondary_phone_mobile})

            if secondary_phones:
                contacts["secondaryContact"]["contactPhones"] = secondary_phones



        # -------------------------------
        # Customer block
        # -------------------------------
        if self.momentum_energy_customer_type == "RESIDENT":
            # Base structure
            customer = {
                "customerType": "RESIDENT",
                "customerSubType": self.momentum_energy_customer_sub_type,
                "communicationPreference": (self.momentum_energy_communication_preference or "").upper(),
                "promotionAllowed": self.momentum_energy_promotion_allowed,
                "contacts": contacts,
            }

            # 🧠 Build resident identity conditionally
            resident_identity = {}

            # 🪪 Passport
            if (
                self.momentum_energy_passport_id
                or self.momentum_energy_passport_expiry
                or self.momentum_energy_passport_country
            ):
                resident_identity["passport"] = {
                    "documentId": self.momentum_energy_passport_id,
                    "documentExpiryDate": (
                        self.momentum_energy_passport_expiry.isoformat()
                        if self.momentum_energy_passport_expiry
                        else None
                    ),
                    "issuingCountry": self.momentum_energy_passport_country,
                }

            # 🚗 Driving License
            if (
                self.momentum_energy_driving_license_id
                or self.momentum_energy_driving_license_expiry
                or self.momentum_energy_driving_license_state
            ):
                resident_identity["drivingLicense"] = {
                    "documentId": self.momentum_energy_driving_license_id,
                    "documentExpiryDate": (
                        self.momentum_energy_driving_license_expiry.isoformat()
                        if self.momentum_energy_driving_license_expiry
                        else None
                    ),
                    "issuingState": self.momentum_energy_driving_license_state,
                }

            # 💳 Medicare
            if (
                self.momentum_energy_medicare_id
                or self.momentum_energy_medicare_number
                or self.momentum_energy_medicare_expiry
            ):
                resident_identity["medicare"] = {
                    "documentId": self.momentum_energy_medicare_id,
                    "documentNumber": self.momentum_energy_medicare_number,
                    "documentExpiryDate": (
                        self.momentum_energy_medicare_expiry.isoformat()
                        if self.momentum_energy_medicare_expiry
                        else None
                    ),
                }

            # ✅ Add only if at least one ID exists
            if resident_identity:
                customer["residentIdentity"] = resident_identity

        else:
            customer = {
                "customerType": "COMPANY",
                "customerSubType": self.momentum_energy_customer_sub_type,
                "communicationPreference": (self.momentum_energy_communication_preference or "").upper(),
                "promotionAllowed": self.momentum_energy_promotion_allowed,
                "companyIdentity": {
                    "industry": self.momentum_energy_industry,
                    "entityName": self.momentum_energy_entity_name,
                    "tradingName": self.momentum_energy_trading_name,
                    "trusteeName": self.momentum_energy_trustee_name,
                    "abn": {"documentId": self.momentum_energy_abn_document_id},
                },
                "contacts": contacts,
            }

            # ✅ Conditionally include 'acn' only if value exists
            if self.momentum_energy_acn_document_id:
                customer["companyIdentity"]["acn"] = {
                    "documentId": self.momentum_energy_acn_document_id
                }



        # -------------------------------
        # Service block
        # -------------------------------
        service = {
            "serviceType": (self.momentum_energy_service_type or "").upper(),
            "serviceSubType": self.momentum_energy_service_sub_type,
            "serviceConnectionId": self.momentum_energy_service_connection_id,
            "estimatedAnnualKwhs": self.momentum_energy_estimated_annual_kwhs,
        }

        if (self.momentum_energy_lot_number):
            service["lotNumber"] = self.momentum_energy_lot_number
        if (self.momentum_energy_service_meter_id):
            service["serviceMeterId"] = self.momentum_energy_service_meter_id    

        # ✅ Conditionally include serviceStartDate only when subtype is not TRANSFER or MOVE IN
        if (
            self.momentum_energy_service_sub_type
            and self.momentum_energy_service_sub_type.upper() not in ["TRANSFER"]
            and self.momentum_energy_service_start_date
        ):
            start_date = self.momentum_energy_service_start_date

            # 🧠 Handle both date and datetime safely
            if isinstance(start_date, datetime):
                dt = start_date.date()
            elif isinstance(start_date, date):
                dt = start_date
            else:
                dt = None

            if dt:
                service["serviceStartDate"] = dt.strftime("%Y-%m-%d")


        # ✅ Build servicedAddress dynamically (skip empty optional fields)
        serviced_address = {
            "streetNumber": self.momentum_energy_service_street_number,
            "streetName": self.momentum_energy_service_street_name,
            "streetTypeCode": self.momentum_energy_service_street_type_code,
            "suburb": self.momentum_energy_service_suburb,
            "state": self.momentum_energy_service_state,
            "postCode": self.momentum_energy_service_post_code,
        }

        if self.momentum_energy_unit_type:
            serviced_address["unitType"]=self.momentum_energy_unit_type

        if self.momentum_energy_service_access_instructions:
            serviced_address["accessInstructions"] = self.momentum_energy_service_access_instructions

        if self.momentum_energy_service_safety_instructions:
            serviced_address["safetyInstructions"] = self.momentum_energy_service_safety_instructions

        service["servicedAddress"] = serviced_address

        # ✅ Build serviceBilling structure
        service["serviceBilling"] = {
            "offerQuoteDate": (
                self.momentum_energy_offer_quote_date.replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
                if self.momentum_energy_offer_quote_date
                else None
            ),
            "serviceOfferCode": self.momentum_energy_service_offer_code,
            "servicePlanCode": self.momentum_energy_service_plan_code,
            "contractTermCode": self.momentum_energy_contract_term_code,
            "contractDate": (
                self.momentum_energy_contract_date.replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
                if self.momentum_energy_contract_date
                else None
            ),
            "paymentMethod": (self.momentum_energy_payment_method or ""),
            "billCycleCode": self.momentum_energy_bill_cycle_code,
            "billDeliveryMethod": (self.momentum_energy_bill_delivery_method or "").upper(),
        }
        # 🟩 Add concession details only when applicable
        if str(self.en_concesion_card_holder or "").strip().lower() == "yes":
            service["serviceBilling"]["concession"] = {
                "concessionCardType": self.momentum_energy_conc_card_type_code,
                "concessionCardCode": self.momentum_energy_conc_card_code,
                "concessionCardNumber": self.momentum_energy_conc_card_number,
                "concessionCardExpiryDate": (
                    self.momentum_energy_conc_card_exp_date.isoformat()
                    if self.momentum_energy_conc_card_exp_date
                    else None
                ),
                "concessionCardFirstName": self.momentum_energy_card_first_name,
                "concessionCardLastName": self.momentum_energy_card_last_name,
                "concessionStartDate": (
                    self.momentum_energy_conc_start_date.isoformat()
                    if self.momentum_energy_conc_start_date
                    else None
                ),
                "concessionEndDate": (
                    self.momentum_energy_conc_end_date.isoformat()
                    if self.momentum_energy_conc_end_date
                    else None
                ),
                "concessionConsentObtained": self.momentum_energy_concession_obtained,
                "concessionHasMS": self.momentum_energy_conc_has_ms,
                "concessionInGroupHome": self.momentum_energy_conc_in_grp_home,
            }

        #  ✅ Add serviceStartDate only when sub type is not TRANSFER or MOVE IN
        if self.momentum_energy_service_sub_type not in ("TRANSFER", "MOVE IN"):
            if self.momentum_energy_service_start_date:
                service["serviceStartDate"] = (
                    self.momentum_energy_service_start_date.isoformat().replace("+00:00", "Z")
                )

        # -------------------------------
        # Final payload
        # -------------------------------
        token = self.env["ir.config_parameter"].sudo().get_param("momentum.jwt_token")
        if not token:
            _logger.error("Bearer token missing for Momentum API for lead %s", self.id)
            raise UserError(
                "Momentum API bearer token missing. Please configure it in System Parameters."
            )

        payload = {
            "transaction": transaction,
            "customer": customer,
            "service": service,
            "token": token,
        }

        _logger.info(
            "Sending Momentum API request for Lead %s, payload:\n%s",
            self.id,
            json.dumps(payload, indent=2, default=str),
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = "http://15.188.138.149/momentum/lead"

        # -------------------------------
        # Request & Error Handling
        # -------------------------------
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            _logger.info(
                "Momentum API response status: %s, response: %s",
                response.status_code,
                response.text,
            )
            # if response.status_code == 200:
            #     data = response.json()
            #     if data.get("success"):
            #         tx_id = data["data"]["data"].get("salesTransactionId")

            #         # Show success notification
            #         return self.env["ir.actions.client"].sudo().create({
            #             "type": "ir.actions.client",
            #             "tag": "display_notification",
            #             "params": {
            #                 "title": "Momentum Success ✅",
            #                 "message": f"Transaction ID: {tx_id}\nLead synced successfully!",
            #                 "type": "success",
            #                 "sticky": True,
            #             }
            #         })
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    tx_id = data["data"]["data"].get("salesTransactionId")
                    self.momentum_transaction_id = tx_id
                    self.is_momentum_submitted = True
                    msg = f"Momentum Success ✅\nTransaction ID: {tx_id}"
                    return
                    # Show success notification to user
                    # raise UserError(msg)

            if not response.ok:
                try:
                    data = response.json()
                    details_str = data.get("details")
                    details = json.loads(details_str) if details_str else {}
                    errors = details.get("errors", [])
                    error_messages = [
                        f"[{err.get('errorCode')}] {err.get('errorMessage')}"
                        for err in errors
                    ]
                    full_error = "\n".join(error_messages) or data.get(
                        "error", "Unknown Momentum API error"
                    )

                    _logger.error(
                        "Momentum API error for Lead %s: %s", self.id, full_error
                    )
                    raise UserError(f"Momentum API Error:\n{full_error}")

                except (ValueError, json.JSONDecodeError):
                    raise UserError(
                        f"Momentum API returned invalid response:\n{response.text}"
                    )

            # ✅ Successful response
            try:
                return response.json()
            except Exception:
                return response.text

        except requests.exceptions.Timeout:
            _logger.error("Momentum API timeout for Lead %s", self.id)
            raise UserError("Momentum API request timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            _logger.exception("Error calling Momentum API for Lead %s", self.id)
            raise UserError(f"Failed to reach Momentum API: {str(e)}")

        return None

    # @api.depends('email_normalized', 'email_from')
    # def _compute_cc_email(self):
    #     for record in self:
    #         record.cc_email = record.email_normalized or record.email_from or ''
