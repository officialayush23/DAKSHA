# app/models/all_models.py
"""
Consolidated Database Models - Agentic Commerce Platform
Matches the complete DB schema (Phases 1-6)

This file contains ALL database models matching the schema exactly.
For request/response DTOs, see app/schemas/schemas.py
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum


# ============================================================================
# PHASE 1: IDENTITY, PRESENCE & CONTEXT
# ============================================================================

class ChannelType(str, Enum):
    """Matches channel_type_enum"""
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    KIOSK = "kiosk"
    VOICE = "voice"
    ADMIN = "admin"


class PresenceStatus(str, Enum):
    """Matches presence_status_enum"""
    ACTIVE = "active"
    IDLE = "idle"
    DISCONNECTED = "disconnected"


class ConversationStatus(str, Enum):
    """Matches conversation_status_enum"""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


# Users (Phase 1)
class User(BaseModel):
    """Matches users table"""
    id: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_active_at: datetime

    class Config:
        from_attributes = True


class UserIdentity(BaseModel):
    """Matches user_identities table"""
    id: str
    user_id: str
    channel: ChannelType
    channel_identifier: str
    verified: bool = False
    last_seen_at: datetime

    class Config:
        from_attributes = True


class PresenceSession(BaseModel):
    """Matches presence_sessions table"""
    id: str
    user_id: Optional[str] = None
    channel: ChannelType
    channel_identifier: str
    connection_id: Optional[str] = None
    status: PresenceStatus = PresenceStatus.ACTIVE
    active_conversation_id: Optional[str] = None
    active_context: Dict[str, Any] = {}
    heartbeat_at: datetime
    last_active_at: datetime
    version: int = 1

    class Config:
        from_attributes = True


class ConversationSession(BaseModel):
    """Matches conversation_sessions table"""
    id: str
    user_id: Optional[str] = None
    started_from: Optional[ChannelType] = None
    state: Dict[str, Any] = {}
    summary: Optional[str] = None
    state_version: int = 1
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationMessage(BaseModel):
    """Matches conversation_messages table"""
    id: str
    session_id: str
    sender: str  # 'user', 'agent', 'tool'
    content: Optional[str] = None
    tool_name: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class BehavioralEvent(BaseModel):
    """Matches behavioral_events table"""
    id: str
    user_id: Optional[str] = None
    event_type: str
    payload: Dict[str, Any] = {}
    captured_at: datetime
    consumed: bool = False

    class Config:
        from_attributes = True


class UserFact(BaseModel):
    """Matches user_facts table"""
    user_id: str
    key: str
    value: Dict[str, Any]
    confidence: float = 1.0
    source: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class UserEmbedding(BaseModel):
    """Matches user_embeddings table"""
    user_id: str
    embedding: List[float]  # vector(1536)
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PHASE 2: PHYSICAL WORLD MODELING
# ============================================================================

class FulfillmentLocationType(str, Enum):
    """Matches fulfillment_location_type_enum"""
    STORE = "store"
    WAREHOUSE = "warehouse"
    DARK_STORE = "dark_store"


class FulfillmentLocation(BaseModel):
    """Matches fulfillment_locations table"""
    id: str
    type: FulfillmentLocationType
    code: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class Store(BaseModel):
    """Matches stores table"""
    id: str
    fulfillment_location_id: str
    store_code: str
    name: str
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Warehouse(BaseModel):
    """Matches warehouses table"""
    id: str
    fulfillment_location_id: str
    warehouse_code: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class LocationZone(BaseModel):
    """Matches location_zones table"""
    id: str
    fulfillment_location_id: str
    zone_code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class LocationBin(BaseModel):
    """Matches location_bins table"""
    id: str
    zone_id: str
    bin_code: str
    height_level: Optional[int] = None

    class Config:
        from_attributes = True


class Product(BaseModel):
    """Matches products table"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    base_price: float
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class ProductVariant(BaseModel):
    """Matches product_variants table"""
    id: str
    product_id: str
    sku: str
    attributes: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class Inventory(BaseModel):
    """Matches inventory table"""
    id: str
    fulfillment_location_id: str
    product_variant_id: str
    zone_id: Optional[str] = None
    bin_id: Optional[str] = None
    quantity_on_hand: int
    quantity_reserved: int = 0  # Matches DB schema
    version: int = 1
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryReservation(BaseModel):
    """Matches inventory_reservations table"""
    id: str
    cart_id: str
    fulfillment_location_id: str
    product_variant_id: str
    quantity: int
    status: str  # 'active', 'released', 'consumed'
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryAlert(BaseModel):
    """Matches inventory_alerts table"""
    id: str
    fulfillment_location_id: str
    product_variant_id: str
    alert_type: str  # 'low_stock', 'out_of_stock', 'manual_override'
    current_quantity: int
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PHASE 3: COMMERCE LIFECYCLE
# ============================================================================

class OrderStatus(str, Enum):
    """Matches order_status_enum"""
    DRAFT = "draft"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class Cart(BaseModel):
    """Matches carts table"""
    id: str
    user_id: Optional[str] = None
    status: str  # 'active', 'abandoned', 'converted'
    version: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    """Matches cart_items table"""
    id: str
    cart_id: str
    product_variant_id: str
    quantity: int
    added_at: datetime

    class Config:
        from_attributes = True


class Order(BaseModel):
    """Matches orders table"""
    id: str
    user_id: Optional[str] = None
    cart_id: Optional[str] = None
    status: OrderStatus = OrderStatus.DRAFT
    total_amount: float
    currency: str = "INR"
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    """Matches order_items table"""
    id: str
    order_id: str
    product_variant_id: str
    fulfillment_location_id: str
    quantity: int
    price_at_purchase: float
    created_at: datetime

    class Config:
        from_attributes = True


class Fulfillment(BaseModel):
    """Matches fulfillments table"""
    id: str
    order_id: str
    fulfillment_location_id: str
    status: Optional[str] = None
    tracking_reference: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Return(BaseModel):
    """Matches returns table"""
    id: str
    order_item_id: str
    reason: Optional[str] = None
    status: str  # 'requested', 'approved', 'rejected', 'completed'
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PHASE 4: MONEY & LEDGER
# ============================================================================

class PaymentStatus(str, Enum):
    """Matches payment_status_enum"""
    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class WalletType(str, Enum):
    """Matches wallet_type_enum"""
    USER = "user"
    ESCROW = "escrow"
    PLATFORM = "platform"


class LedgerEntryType(str, Enum):
    """Matches ledger_entry_type_enum"""
    DEBIT = "debit"
    CREDIT = "credit"


class PaymentProvider(BaseModel):
    """Matches payment_providers table"""
    id: str
    name: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class Payment(BaseModel):
    """Matches payments table"""
    id: str
    order_id: str
    provider_id: str
    status: PaymentStatus
    amount: float
    currency: str = "INR"
    idempotency_key: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentEvent(BaseModel):
    """Matches payment_events table"""
    id: str
    payment_id: str
    provider_event_id: Optional[str] = None
    event_type: Optional[str] = None
    payload: Dict[str, Any]
    processed: bool = False
    received_at: datetime

    class Config:
        from_attributes = True


class PaymentAttempt(BaseModel):
    """Matches payment_attempts table"""
    id: str
    payment_id: str
    gateway_reference: Optional[str] = None
    status: Optional[str] = None
    raw_response: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class Wallet(BaseModel):
    """Matches wallets table"""
    id: str
    wallet_type: WalletType
    owner_user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LedgerEntry(BaseModel):
    """Matches ledger_entries table"""
    id: str
    wallet_id: str
    entry_type: LedgerEntryType
    amount: float
    reference_type: str
    reference_id: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Refund(BaseModel):
    """Matches refunds table"""
    id: str
    payment_id: str
    amount: float
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PHASE 5: OPS, SUPPORT & HUMAN HANDOFF
# ============================================================================

class OpsRole(str, Enum):
    """Matches ops_role_enum"""
    SUPPORT_AGENT = "support_agent"
    FULFILLMENT_AGENT = "fulfillment_agent"
    OPS_MANAGER = "ops_manager"
    ADMIN = "admin"


class TicketStatus(str, Enum):
    """Matches ticket_status_enum"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    AWAITING_USER = "awaiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketType(str, Enum):
    """Matches ticket_type_enum"""
    ORDER_ISSUE = "order_issue"
    PAYMENT_ISSUE = "payment_issue"
    INVENTORY_ISSUE = "inventory_issue"
    DELIVERY_ISSUE = "delivery_issue"
    GENERAL = "general"


class HandoffStatus(str, Enum):
    """Matches handoff_status_enum"""
    PENDING = "pending"
    CLAIMED = "claimed"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class HandoffReason(str, Enum):
    """Matches handoff_reason_enum"""
    LOW_CONFIDENCE = "low_confidence"
    PAYMENT_FAILURE = "payment_failure"
    INVENTORY_CONFLICT = "inventory_conflict"
    USER_REQUEST = "user_request"
    POLICY_VIOLATION = "policy_violation"
    HIGH_VALUE_ORDER = "high_value_order"
    ANGER_DETECTED = "anger_detected"


class OpsUser(BaseModel):
    """Matches ops_users table"""
    id: str
    role: OpsRole
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class SupportTicket(BaseModel):
    """Matches support_tickets table"""
    id: str
    user_id: str
    order_id: Optional[str] = None
    ticket_type: TicketType
    status: TicketStatus = TicketStatus.OPEN
    subject: str
    description: Optional[str] = None
    priority: str = "medium"  # 'low', 'medium', 'high', 'urgent'
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportTicketEvent(BaseModel):
    """Matches support_ticket_events table"""
    id: str
    ticket_id: str
    actor_type: str  # 'user', 'agent', 'ops'
    actor_id: Optional[str] = None
    action: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HumanHandoff(BaseModel):
    """Matches human_handoffs table"""
    id: str
    conversation_id: str
    user_id: str
    reason: HandoffReason
    confidence_score: Optional[float] = None
    context_snapshot: Dict[str, Any]
    status: HandoffStatus = HandoffStatus.PENDING
    claimed_by: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpsOverride(BaseModel):
    """Matches ops_overrides table"""
    id: str
    ops_user_id: str
    target_type: str  # 'order', 'inventory', 'payment'
    target_id: str
    action: str
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class SLAPolicy(BaseModel):
    """Matches sla_policies table"""
    id: str
    ticket_type: TicketType
    priority: str
    response_time_minutes: int
    resolution_time_minutes: int

    class Config:
        from_attributes = True


class SLABreach(BaseModel):
    """Matches sla_breaches table"""
    id: str
    ticket_id: str
    breached_at: datetime
    breach_type: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# PHASE 6: AGENTIC INTELLIGENCE
# ============================================================================

class AgentTrigger(str, Enum):
    """Matches agent_trigger_enum"""
    CHAT = "chat"
    SYSTEM = "system"
    CRON = "cron"
    WEBHOOK = "webhook"


class Agent(BaseModel):
    """Matches agents table"""
    name: str
    description: str
    responsibility: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class AgentRun(BaseModel):
    """Matches agent_runs table"""
    id: str
    agent_name: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    trigger: AgentTrigger
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentProposal(BaseModel):
    """Matches agent_proposals table"""
    id: str
    agent_run_id: str
    proposal_type: str
    proposal_payload: Dict[str, Any]
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrchestrationDecision(BaseModel):
    """Matches orchestration_decisions table"""
    id: str
    conversation_id: str
    decision_type: str  # 'accept', 'reject', 'merge', 'escalate'
    accepted_proposal_ids: List[str] = []
    rejected_proposal_ids: List[str] = []
    reason: str
    decided_by: str = "system"  # 'system', 'human'
    created_at: datetime

    class Config:
        from_attributes = True


class AgentCommit(BaseModel):
    """Matches agent_commits table"""
    id: str
    orchestration_decision_id: str
    commit_type: str
    commit_payload: Dict[str, Any]
    commit_status: str  # 'success', 'failed', 'rejected'
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentBudget(BaseModel):
    """Matches agent_budgets table"""
    agent_name: str
    max_tokens_per_run: int
    max_latency_ms: int
    max_calls_per_conversation: int

    class Config:
        from_attributes = True


class AgentCache(BaseModel):
    """Matches agent_cache table"""
    cache_key: str
    agent_name: str
    response: Dict[str, Any]
    expires_at: datetime

    class Config:
        from_attributes = True


class Recommendation(BaseModel):
    """Matches recommendations table"""
    id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    reasoning_summary: str
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationItem(BaseModel):
    """Matches recommendation_items table"""
    id: str
    recommendation_id: str
    product_variant_id: str
    rank: int
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class PromotionCandidate(BaseModel):
    """Matches promotion_candidates table"""
    id: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    promotion_id: Optional[str] = None
    expected_benefit: Optional[float] = None
    reasoning: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ADDITIONAL MODELS (Referenced in code but need verification)
# ============================================================================

class UserAddress(BaseModel):
    """User addresses - referenced in code, verify in DB"""
    id: str
    user_id: str
    type: str = "home"
    address_line: str
    city: str
    pincode: str
    is_default: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserPaymentMethod(BaseModel):
    """User payment methods - referenced in code, verify in DB"""
    id: str
    user_id: str
    provider: str
    gateway_token_id: str
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    is_default: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ProductReview(BaseModel):
    """Product reviews - referenced in code, verify in DB"""
    id: str
    product_id: str
    user_id: str
    rating: int
    review_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
