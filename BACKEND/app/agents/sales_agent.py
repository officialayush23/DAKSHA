# app/agents/sales_agent.py
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.fulfillment_agent import FulfillmentAgent
from app.agents.loyalty_agent import LoyaltyAgent
from app.agents.support_agent import SupportAgent

class SalesAgent:
    def __init__(self, db, user_id, session_id, channel):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.channel = channel

    def handle(self, intent: str, payload: dict):
        if intent == "DISCOVER":
            return RecommendationAgent(self.db, self.user_id).recommend(payload)

        if intent == "CHECK_STOCK":
            return InventoryAgent(self.db).check(payload)

        if intent == "ADD_TO_CART":
            return InventoryAgent(self.db).reserve(payload)

        if intent == "CHECKOUT":
            return PaymentAgent(self.db, self.user_id).initiate(payload)

        if intent == "PAYMENT_FAILED":
            return PaymentAgent(self.db, self.user_id).retry(payload)

        if intent == "FULFILL":
            return FulfillmentAgent(self.db).schedule(payload)

        if intent == "APPLY_OFFERS":
            return LoyaltyAgent(self.db, self.user_id).apply(payload)

        if intent == "POST_PURCHASE":
            return SupportAgent(self.db, self.user_id).handle(payload)

        return {"message": "I didn’t understand that"}
