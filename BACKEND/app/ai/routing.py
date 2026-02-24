# app/ai/routing.py
# decides which agent should handle the next turn based on the conversation state and context
from pydantic import BaseModel, Field
from typing import Literal

class RouteSchema(BaseModel):
    next_agent: Literal[
        "FINISH", 
        "RecommendationAgent", 
        "InventoryAgent",
        "CheckoutAgent", 
        "SupportAgent", 
        "LoyaltyAgent",
        "Handoff"
    ] = Field(description="The next agent to route the conversation to.")
    reasoning: str = Field(description="Why this agent was chosen based on the user's intent.")