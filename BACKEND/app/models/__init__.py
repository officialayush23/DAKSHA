"""
Models - Database Models
All models consolidated in all_models.py
"""

from app.models.all_models import *

# Export all models for backward compatibility
__all__ = [
    # Phase 1: Identity & Context
    "User", "UserIdentity", "PresenceSession", "ConversationSession",
    "ConversationMessage", "BehavioralEvent", "UserFact", "UserEmbedding",
    "ChannelType", "PresenceStatus", "ConversationStatus",
    
    # Phase 2: Physical World
    "FulfillmentLocation", "Store", "Warehouse", "LocationZone", "LocationBin",
    "Product", "ProductVariant", "Inventory", "InventoryReservation", "InventoryAlert",
    "FulfillmentLocationType",
    
    # Phase 3: Commerce
    "Cart", "CartItem", "Order", "OrderItem", "Fulfillment", "Return",
    "OrderStatus",
    
    # Phase 4: Money
    "Payment", "PaymentEvent", "PaymentAttempt", "Wallet", "LedgerEntry", "Refund",
    "PaymentProvider", "PaymentStatus", "WalletType", "LedgerEntryType",
    
    # Phase 5: Ops & Support
    "OpsUser", "SupportTicket", "SupportTicketEvent", "HumanHandoff", "OpsOverride",
    "SLAPolicy", "SLABreach", "OpsRole", "TicketStatus", "TicketType",
    "HandoffStatus", "HandoffReason",
    
    # Phase 6: Agents
    "Agent", "AgentRun", "AgentProposal", "OrchestrationDecision", "AgentCommit",
    "AgentBudget", "AgentCache", "Recommendation", "RecommendationItem", "PromotionCandidate",
    "AgentTrigger",
    
    # Additional
    "UserAddress", "UserPaymentMethod", "ProductReview",
]
