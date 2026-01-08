# app/core/rpc.py

"""
Database RPC Functions - Authoritative Write Path
All transactional writes go through these RPCs.
No direct table updates for: inventory, orders, payments, fulfillments, ledger_entries
"""

from fastapi import HTTPException
from app.core.database import supabase
from typing import Optional
import logging

logger = logging.getLogger("daksha.rpc")


class RPCService:
    """
    Wrapper for all database RPC functions.
    These are the ONLY way to mutate transactional data.
    """

    # ============================================================================
    # INVENTORY RPCs
    # ============================================================================

    @staticmethod
    def reserve_inventory(
        user_id: str,
        cart_id: str,
        variant_id: str,
        location_id: str,
        quantity: int,
        expires_at: Optional[str] = None,
    ) -> str:
        """
        Reserve inventory for a cart.
        Matches final specification signature.
        Returns reservation_id (uuid)
        """
        try:
            result = supabase.rpc(
                "reserve_inventory",
                {
                    "p_user_id": user_id,
                    "p_cart_id": cart_id,
                    "p_variant_id": variant_id,
                    "p_location_id": location_id,
                    "p_quantity": quantity,
                    "p_expires_at": expires_at,
                }
            ).execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data
            return result
        except Exception as e:
            logger.error(f"RPC reserve_inventory failed: {e}")
            raise HTTPException(500, f"Failed to reserve inventory: {str(e)}")

    @staticmethod
    def release_inventory_reservation(reservation_id: str) -> None:
        """
        Release an inventory reservation.
        """
        try:
            supabase.rpc(
                "release_inventory_reservation",
                {"p_reservation_id": reservation_id}
            ).execute()
        except Exception as e:
            logger.error(f"RPC release_inventory_reservation failed: {e}")
            raise HTTPException(500, f"Failed to release reservation: {str(e)}")

    @staticmethod
    def commit_inventory_for_order(order_id: str) -> None:
        """
        Commit inventory reservations for an order (when order is paid).
        """
        try:
            supabase.rpc(
                "commit_inventory_for_order",
                {"p_order_id": order_id}
            ).execute()
        except Exception as e:
            logger.error(f"RPC commit_inventory_for_order failed: {e}")
            raise HTTPException(500, f"Failed to commit inventory: {str(e)}")

    @staticmethod
    def adjust_inventory(
        variant_id: str,
        location_id: str,
        delta: int,
        reason: str,
    ) -> None:
        """
        Adjust inventory quantity (positive or negative delta).
        """
        try:
            supabase.rpc(
                "adjust_inventory",
                {
                    "p_variant_id": variant_id,
                    "p_location_id": location_id,
                    "p_delta": delta,
                    "p_reason": reason,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC adjust_inventory failed: {e}")
            raise HTTPException(500, f"Failed to adjust inventory: {str(e)}")

    # ============================================================================
    # ORDER RPCs
    # ============================================================================

    @staticmethod
    def create_order_from_cart(
        user_id: str,
        cart_id: str,
        order_type: str,
        fulfillment_location_id: Optional[str] = None,
        address_id: Optional[str] = None,
    ) -> str:
        """
        Create order from cart.
        Returns order_id (uuid)
        """
        try:
            result = supabase.rpc(
                "create_order_from_cart",
                {
                    "p_user_id": user_id,
                    "p_cart_id": cart_id,
                    "p_order_type": order_type,
                    "p_fulfillment_location_id": fulfillment_location_id,
                    "p_address_id": address_id,
                }
            ).execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data
            return result
        except Exception as e:
            logger.error(f"RPC create_order_from_cart failed: {e}")
            raise HTTPException(500, f"Failed to create order: {str(e)}")

    @staticmethod
    def transition_order_state(
        order_id: str,
        from_state: str,
        to_state: str,
    ) -> None:
        """
        Transition order state (enforces FSM).
        """
        try:
            supabase.rpc(
                "transition_order_state",
                {
                    "p_order_id": order_id,
                    "p_from_state": from_state,
                    "p_to_state": to_state,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC transition_order_state failed: {e}")
            raise HTTPException(500, f"Failed to transition order state: {str(e)}")

    @staticmethod
    def mark_order_paid(order_id: str) -> None:
        """
        Mark order as paid.
        """
        try:
            supabase.rpc(
                "mark_order_paid",
                {"p_order_id": order_id}
            ).execute()
        except Exception as e:
            logger.error(f"RPC mark_order_paid failed: {e}")
            raise HTTPException(500, f"Failed to mark order paid: {str(e)}")

    @staticmethod
    def cancel_order(order_id: str, reason: str) -> None:
        """
        Cancel an order.
        """
        try:
            supabase.rpc(
                "cancel_order",
                {
                    "p_order_id": order_id,
                    "p_reason": reason,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC cancel_order failed: {e}")
            raise HTTPException(500, f"Failed to cancel order: {str(e)}")

    # ============================================================================
    # FULFILLMENT RPCs
    # ============================================================================

    @staticmethod
    def create_fulfillment_for_order(order_id: str) -> str:
        """
        Create fulfillment for an order.
        Returns fulfillment_id (uuid)
        """
        try:
            result = supabase.rpc(
                "create_fulfillment_for_order",
                {"p_order_id": order_id}
            ).execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data
            return result
        except Exception as e:
            logger.error(f"RPC create_fulfillment_for_order failed: {e}")
            raise HTTPException(500, f"Failed to create fulfillment: {str(e)}")

    # ============================================================================
    # PAYMENT RPCs
    # ============================================================================

    @staticmethod
    def capture_payment_to_escrow(
        payment_id: str,
        escrow_wallet_id: str,
    ) -> None:
        """
        Capture payment to escrow wallet.
        """
        try:
            supabase.rpc(
                "capture_payment_to_escrow",
                {
                    "p_payment_id": payment_id,
                    "p_escrow_wallet_id": escrow_wallet_id,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC capture_payment_to_escrow failed: {e}")
            raise HTTPException(500, f"Failed to capture payment: {str(e)}")

    @staticmethod
    def refund_to_user_wallet(
        refund_id: str,
        user_wallet_id: str,
        escrow_wallet_id: str,
    ) -> None:
        """
        Refund payment to user wallet.
        """
        try:
            supabase.rpc(
                "refund_to_user_wallet",
                {
                    "p_refund_id": refund_id,
                    "p_user_wallet_id": user_wallet_id,
                    "p_escrow_wallet_id": escrow_wallet_id,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC refund_to_user_wallet failed: {e}")
            raise HTTPException(500, f"Failed to refund: {str(e)}")

    @staticmethod
    def assert_order_paid(
        order_id: str,
        escrow_wallet_id: str,
    ) -> None:
        """
        Assert that order has captured funds in escrow.
        """
        try:
            supabase.rpc(
                "assert_order_paid",
                {
                    "p_order_id": order_id,
                    "p_escrow_wallet_id": escrow_wallet_id,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC assert_order_paid failed: {e}")
            raise HTTPException(500, f"Order payment assertion failed: {str(e)}")

    # ============================================================================
    # HANDOFF RPCs
    # ============================================================================

    @staticmethod
    def claim_handoff(handoff_id: str, ops_user_id: str) -> None:
        """
        Claim a human handoff.
        """
        try:
            supabase.rpc(
                "claim_handoff",
                {
                    "p_handoff_id": handoff_id,
                    "p_ops_user_id": ops_user_id,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC claim_handoff failed: {e}")
            raise HTTPException(500, f"Failed to claim handoff: {str(e)}")

    @staticmethod
    def resolve_handoff(handoff_id: str, ops_user_id: str) -> None:
        """
        Resolve a human handoff.
        """
        try:
            supabase.rpc(
                "resolve_handoff",
                {
                    "p_handoff_id": handoff_id,
                    "p_ops_user_id": ops_user_id,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC resolve_handoff failed: {e}")
            raise HTTPException(500, f"Failed to resolve handoff: {str(e)}")

    @staticmethod
    def propose_handoff(
        agent_run_id: str,
        reason: str,
        confidence: float,
        context: dict,
    ) -> None:
        """
        Propose a human handoff from an agent.
        """
        try:
            supabase.rpc(
                "propose_handoff",
                {
                    "p_agent_run_id": agent_run_id,
                    "p_reason": reason,
                    "p_confidence": confidence,
                    "p_context": context,
                }
            ).execute()
        except Exception as e:
            logger.error(f"RPC propose_handoff failed: {e}")
            raise HTTPException(500, f"Failed to propose handoff: {str(e)}")
