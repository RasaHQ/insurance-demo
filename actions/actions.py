"""Custom actions"""
import json
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
        slots = {
            "AA_CONTINUE_FORM": None,
            "zz_confirm_form": None,
            "age": None
        }
        if tracker.get_slot("zz_confirm_form") == "yes":
            dispatcher.utter_message("Here is your quote...")
        else:
            dispatcher.utter_message("Canceled.")

        return [SlotSet(slot, value) for slot, value in slots.items()]


class ActionRecentClaims(Action):

    def name(self) -> Text:
        return "action_ask_recent_claims"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:

        dispatcher.utter_message("Here are your claims...")

        return []


class ValidateQuoteForm(CustomFormValidationAction):
    """Validates Slots for the Quote form."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "validate_quote_form"

    async def validate_age(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validates value of 'amount-of-money' slot"""
        age = tracker.get_slot("age")

        try:
            int(age) == age
        except ValueError:
            dispatcher.utter_message(template="utter_age_invalid")
            return {"age": None}

        return {"age": age}

    async def explain_age(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Explains 'credit_card' slot"""
        dispatcher.utter_message("Actions Age")

        return {}


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

        # TODO: Update for the profile data once it's created.
        dispatcher.utter_message("Your claim is still under review.")

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
        valid_claims = [
            "123456",
            "234567"
        ]
        claim_id = tracker.get_slot("claim_id")

        print("claim", claim_id)
        print(tracker.slots)

        if str(claim_id) not in valid_claims:
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

