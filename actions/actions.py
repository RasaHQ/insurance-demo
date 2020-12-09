"""Custom actions"""
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
)
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

from actions.custom_forms import CustomFormValidationAction


logger = logging.getLogger(__name__)


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


class AskConfirmAddress(Action):
    def name(self) -> Text:
        return "action_ask_verify_address"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        dispatcher.utter_message(template="utter_confirm_address")
        return []


class ActionNewIdCard(Action):

    def name(self) -> Text:
        return "action_new_id_card_form"


class ValidateNewIdCardForm(CustomFormValidationAction):
    """Validates data entered into the Claim Status Form."""

    def name(self) -> Text:
        """Unique identifier for the action."""
        return "validate_new_id_card_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Optional[List[Text]]:
        additional_slots = []

        # If a member knows their claim ID then ask them. Otherwise, show them the status of some recent claims.
        if tracker.slots.get("verify_address") == "/affirm":
            additional_slots.append("claim_id")
        elif tracker.slots.get("verify_address") == "/deny":
            additional_slots.append("recent_claims")

        return additional_slots + slots_mapped_in_domain


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

