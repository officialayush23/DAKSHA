# app/agents/registry.py
from enum import Enum

class AgentType(str, Enum):
    RECOMMENDATION = "recommendation"
    INVENTORY = "inventory"
    PAYMENT = "payment"
    FULFILLMENT = "fulfillment"
    LOYALTY = "loyalty"
    SUPPORT = "support"
