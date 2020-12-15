"""Custom actions"""
import json
import datetime
from typing import Dict, Text, Any, List, Optional
import logging
from dateutil import parser
from rasa_sdk.interfaces import Action
from rasa_sdk.events import (
    SlotSet,
    EventType,
    ActionExecuted,
    SessionStarted,
    Restarted,
    FollowupAction,
    UserUtteranceReverted,
    ActionExecutionRejected
)
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

from actions.custom_forms import CustomFormValidationAction


logger = logging.getLogger(__name__)

MOCK_DATA = json.load(open("actions/mock_data.json", "r"))

US_STATES = ["AZ", "AL", "AK", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
             "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
             "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


class AskConfirmAddress(Action):
    """Retrieves existing user address and asks for the user to verify the address."""

    def name(self) -> Text:
        return "action_ask_verify_address"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        # Load the member address from the JSON document.
        address_slots = {
            "address_street": MOCK_DATA["member_info"]["home_address"]["address_street"],
            "address_city": MOCK_DATA["member_info"]["home_address"]["address_city"],
            "address_state": MOCK_DATA["member_info"]["home_address"]["address_state"],
            "address_zip": MOCK_DATA["member_info"]["home_address"]["address_zip"]
        }

        # Build the full address.
        address_line_two = f"{address_slots['address_city']}, {address_slots['address_state']} " \
                           f"{address_slots['address_zip']}"
        full_address = "\n".join([address_slots['address_street'], address_line_two])
        address_slots["full_address"] = full_address

        dispatcher.utter_message(template="utter_confirm_address", **address_slots)

        return [SlotSet(k, v) for k, v in address_slots.items()]


class ActionVerifyAddress(Action):
    """Checks if the user confirms their address or not."""

    def name(self) -> Text:
        return "action_verify_address_form"

    def run(
        self, dispather: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        address_slots = ["address_street",
                         "address_city",
                         "address_state",
                         "address_zip"]

        verify_address = tracker.get_slot("verify_address")

        # Reset the address slots if user doesn't verify address so the change address form can collect new address.
        if not verify_address:
            return [SlotSet(a, None) for a in address_slots]

        return [SlotSet("verify_address", verify_address)]


class ValidateVerifyAddressForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_verify_address_form"

    async def validate_verify_address(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        verify_address = tracker.get_slot("verify_address")

        return {"verify_address": verify_address}


class ActionUpdateAddress(Action):

    def name(self) -> Text:
        return "action_update_address"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        address_street = tracker.get_slot("address_street")
        address_city = tracker.get_slot("address_city")
        address_state = tracker.get_slot("address_state")
        address_zip = tracker.get_slot("address_zip")

        address_line_two = f"{address_city}, {address_state} {address_zip}"
        full_address = "\n".join([address_street, address_line_two])

        dispatcher.utter_message("Thank you! Your address has been changed to:")
        dispatcher.utter_message(full_address)

        # Update the address in the data.
        MOCK_DATA["member_info"]["home_address"] = {
            "address_street": address_street,
            "address_city": address_city,
            "address_state": address_state,
            "address_zip": address_zip
        }

        return [SlotSet("verify_address", None)]


class ValidateChangeAddressForm(FormValidationAction):
    """Validates the user has filled out the change of address form correctly."""

    def name(self) -> Text:
        return "validate_change_address_form"

    async def validate_address_state(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if value not in US_STATES:
            dispatcher.utter_message(f"{value} is invalid. Please provide a valid state.")
            return {"address_state": None}

        return {"address_state": value}


class ActionNewIdCard(Action):

    def name(self) -> Text:
        return "action_new_id_card"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        dispatcher.utter_message("Thank you! We'll send you a new ID card.")

        return []


class ActionGetQuote(Action):
    """Gets an insurance quote"""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "action_get_quote"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Executes the action"""
        slots = ["quote_insurance_type", "quote_state", "quote_number_persons"]

        # Build the quote from the provided data.
        insurance_type = tracker.get_slot("quote_insurance_type")
        n_persons = int(tracker.get_slot("quote_number_persons"))

        baseline_rate = MOCK_DATA["policy_quote"]["insurance_type"][insurance_type]
        final_quote = baseline_rate * n_persons

        msg_params = {
            "final_quote": final_quote,
            "insurance_type": insurance_type.capitalize(),
            "quote_state": tracker.get_slot("quote_state"),
            "n_persons": n_persons
        }
        dispatcher.utter_message(template="utter_final_quote", **msg_params)

        # Reset the slot values.
        return [SlotSet(slot, None) for slot in slots]


class ValidateQuoteForm(FormValidationAction):
    """Validates Slots for the Quote form."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "validate_quote_form"

    async def validate_quote_insurance_type(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validates value of 'amount-of-money' slot"""
        insurance_type = tracker.get_slot("quote_insurance_type")

        if insurance_type.lower() not in ["auto", "health", "life", "home"]:
            dispatcher.utter_message("Must select a valid type of insurance")
            return {"quote_insurance_type": None}

        return {"quote_insurance_type": insurance_type}

    async def validate_quote_state(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validates the state provided by user to get an insurance quote."""
        if value not in US_STATES:
            dispatcher.utter_message(f"{value} is invalid. Please provide a valid state.")
            return {"quote_state": None}

        return {"quote_state": value}

    async def validate_quote_number_persons(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        """Validates the number of persons entered is valid."""
        try:
            int(value)
        except TypeError:
            dispatcher.utter_message(f"Number of persons must be an integer.")
            return {"quote_number_persons": None}

        if int(value) <= 0:
            dispatcher.utter_message("Number of people on policy must be >= 1.")
            return {"quote_number_persons": None}

        return {"quote_number_persons": value}


class ActionRecentClaims(Action):

    def name(self) -> Text:
        return "action_ask_recent_claims"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        # Get the claims on the page.
        claim_page = tracker.get_slot("page")

        # Get the first initial page of claims.
        if claim_page is None:
            scroll_response = claims_scroll(claim_page, "init")
        else:
            scroll_response = claims_scroll(claim_page, "next")

        for c in scroll_response["claims"]:
            dispatcher.utter_message(template="utter_claim_detail", **c)

        return [SlotSet("page", scroll_response["page"])]


class ActionClaimStatus(Action):
    """Gets the status of the user's last claim."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "action_claim_status"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        # Get the claim provided by the user.
        user_clm_id = tracker.get_slot("claim_id")
        clm = next((c for c in MOCK_DATA["claims"] if str(c["claim_id"]) == user_clm_id), None)

        # Display details about the selected claims.
        if clm:
            formatted_date = str(datetime.datetime.strptime(str(clm["claim_date"]), "%Y%m%d").date())
            clm_params = {
                "claim_date": formatted_date,
                "claim_id": clm["claim_id"],
                "claim_balance": f"${str(clm['claim_balance'])}",
                "claim_status": clm["claim_status"]
            }
            dispatcher.utter_message(template="utter_claim_detail", **clm_params)
        else:
            dispatcher.utter_message("I don't know that claim...")

        reset_slots = ["knows_claim_id", "AA_CONTINUE_FORM", "zz_confirm_form"]
        return [SlotSet(slot, None) for slot in reset_slots]


class ValidateGetClaimForm(FormValidationAction):
    """Validates data entered into the Get Claim Form."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "validate_get_claim_form"

    async def validate_claim_id(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Checks if the claim ID is valid for the member."""
        user_claims = MOCK_DATA["claims"]
        claim_id = tracker.get_slot("claim_id")

        if str(claim_id) not in [clm["claim_id"] for clm in user_claims]:
            dispatcher.utter_message("The Claim ID you entered is not valid. Please check and try again.")
            return {"claim_id": None}
        else:
            return {"claim_id": claim_id}


class ValidateClaimStatusForm(CustomFormValidationAction):
    """Validates data entered into the Claim Status Form."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "validate_claim_status_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Optional[List[Text]]:
        additional_slots = []

        # If a member knows their claim ID then ask them. Otherwise, show them the status of some recent claims.
        if tracker.slots.get("knows_claim_id") == "/affirm":
            additional_slots.append("claim_id")
        elif tracker.slots.get("knows_claim_id") == "/deny":
            additional_slots.append("recent_claims")

        return additional_slots + slots_mapped_in_domain

    async def extract_recent_claims(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots["requested_slot"] == "recent_claims":
            text_of_last_user_message = tracker.latest_message.get("text")

            return {"recent_claims": text_of_last_user_message}

    async def extract_claim_id(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots["requested_slot"] == "claim_id":
            text_of_last_user_message = tracker.latest_message.get("text")

            return {"claim_id": text_of_last_user_message}

    async def validate_claim_id(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Checks if the claim ID is valid for the member."""
        valid_claims = [
            "123456",
            "234567"
        ]
        claim_id = tracker.get_slot("claim_id")

        print("claim other validate", claim_id)

        if str(claim_id) not in valid_claims:
            dispatcher.utter_message("The Claim ID you entered is not valid. Please check and try again.")
            return {"claim_id": None}

        return {"claim_id": claim_id}


class ActionValidateScrollClaims(FormValidationAction):

    def name(self) -> Text:
        return "validate_scroll_claims_form"

    async def validate_scroll_status(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        # Get the claims on the page.
        claim_page = tracker.get_slot("page")
        scroll_status = value

        if scroll_status == "cancel":
            return {"scroll_status": "stop"}

        scroll_response = claims_scroll(claim_page, scroll_status)

        for c in scroll_response["claims"]:
            dispatcher.utter_message(template="utter_claim_detail", **c)

        return {"scroll_status": None, "page": scroll_response["page"]}


class ActionPayClaim(Action):
    """Gets the status of the user's last claim."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "action_pay_claim"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        # Get the claim provided by the user.
        user_clm_id = tracker.get_slot("claim_id")
        amount_to_pay = tracker.get_slot("payment_amount")
        claim_balance = tracker.get_slot("claim_balance")

        msg_params = {
            "claim_id": user_clm_id,
            "amount_to_pay": amount_to_pay,
            "claim_balance": claim_balance - amount_to_pay
        }
        for c in MOCK_DATA["claims"]:
            if c["claim_id"] == user_clm_id:
                c.update({"claim_balance": claim_balance - amount_to_pay})

        dispatcher.utter_message(template="utter_claim_payment_success", **msg_params)

        reset_slots = ["claim_balance", "payment_amount", "confirm_payment"]
        return [SlotSet(slot, None) for slot in reset_slots]


class ActionCancelPayment(Action):
    """Cancels the payment form."""

    def name(self) -> Text:
        return "action_cancel_payment"

    async def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        dispatcher.utter_message(template="utter_cancel_payment")

        reset_slots = ["claim_balance", "payment_amount", "claim_id", "confirm_payment"]
        return [SlotSet(slot, None) for slot in reset_slots]


class ValidatePayClaimForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_pay_claim_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:
        additional_slots = []
        if tracker.slots.get("claim_balance"):
            claim_id = tracker.slots.get("claim_id")
            if tracker.slots.get("claim_balance") > 0:
                additional_slots.append("payment_amount")
                additional_slots.append("confirm_payment")

        return additional_slots + slots_mapped_in_domain

    async def extract_payment_amount(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots["requested_slot"] == "payment_amount":
            text_of_last_user_message = tracker.latest_message.get("text")

            return {"payment_amount": text_of_last_user_message}

    async def extract_confirm_payment(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        if tracker.slots["requested_slot"] == "confirm_payment":
            text_of_last_user_message = tracker.latest_message.get("text")

            return {"confirm_payment": text_of_last_user_message}

    async def validate_claim_id(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Checks if the claim ID is valid for the member."""
        user_claims = MOCK_DATA["claims"]
        claim_id = tracker.get_slot("claim_id")

        if str(claim_id) not in [clm["claim_id"] for clm in user_claims]:
            dispatcher.utter_message("The Claim ID you entered is not valid. Please check and try again.")
            return {"claim_id": None}
        else:
            clm = next((c for c in MOCK_DATA["claims"] if str(c["claim_id"]) == claim_id), None)
            return {"claim_id": claim_id, "claim_balance": clm["claim_balance"]}

    async def validate_payment_amount(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        user_claims = MOCK_DATA["claims"]
        claim_id = tracker.get_slot("claim_id")
        payment_amount = tracker.get_slot("payment_amount")
        clm = next((c for c in MOCK_DATA["claims"] if str(c["claim_id"]) == claim_id), None)

        # Check that a valid number is provided.
        try:
            payment_amount = float(payment_amount)
        except TypeError:
            dispatcher.utter_message("Please enter a valid number as your payment amount.")
            return {"payment_amount": None}

        # Check that the payment is greater than zero.
        if payment_amount <= 0:
            dispatcher.utter_message("Your payment must be greater than $0.")
            return {"payment_amount": None}

        # Check that the payment amount doesn't exceed the amount owed on the claim.
        if payment_amount > clm["claim_balance"]:
            dispatcher.utter_message(f"The amount you want to pay, ${str(payment_amount)}, is greater than the amount "
                                     f"owed, ${str(clm['claim_balance'])}")
            return {"payment_amount": clm["claim_balance"], "claim_balance": clm["claim_balance"]}

        return {"payment_amount": payment_amount, "claim_balance": clm["claim_balance"]}


def claims_scroll(curr_page, scroll_status):
    """Performs the query to get claims on the specified page."""
    if curr_page is None:
        curr_page = 0

    if scroll_status == "next":
        if curr_page >= 0:
            curr_page += 1
        idx_start = curr_page * 2
        idx_end = idx_start + 2
    elif scroll_status == "init":
        idx_start = 0
        idx_end = idx_start + 2
    else:
        if curr_page > 0:
            curr_page -= 1
        idx_start = curr_page * 2
        idx_end = idx_start + 2

    # Get claims on the page.
    page_claims = MOCK_DATA["claims"][idx_start:idx_end]
    formatted_claims = []
    for clm in page_claims:
        formatted_date = str(datetime.datetime.strptime(str(clm["claim_date"]), "%Y%m%d").date())
        clm_params = {
            "claim_date": formatted_date,
            "claim_id": clm["claim_id"],
            "claim_balance": f"${str(clm['claim_balance'])}",
            "claim_status": clm["claim_status"]
        }

        formatted_claims.append(clm_params)

    return {"page": curr_page, "claims": formatted_claims}
