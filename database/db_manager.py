from pymongo import MongoClient


class DBManager:
    def __init__(self, connection_str) -> None:
        self.__db = MongoClient(connection_str)["database"]

    def create_claim(self, claim):
        self.__db["claims"].insert_one(claim)

    def get_claims(self):
        return list(self.__db["claims"].find())

    def update_claim_balance(self, claim_id, new_balance):
        self.__db["claims"].update_one({"claim_id": claim_id}, {"$set": {"claim_balance": new_balance}})

    def get_baseline_rate(self, insurance_type):
        return list(self.__db["policy_quote"].find({}, {"insurance_type": {insurance_type: 1}}))[0]["insurance_type"][insurance_type]

    def get_home_address(self):
        return list(self.__db["member_info"].find({}, {"home_address": 1}))[0]["home_address"]

    def update_home_address(self, new_home_address):
        _id = list(self.__db["member_info"].find())[0]["_id"]
        self.__db["member_info"].update_one({"_id": _id}, {"$set": {"home_address": new_home_address}})

    def get_states(self):
        return list(self.__db["us_states"].find())[0]["states"]
