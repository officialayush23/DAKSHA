import os
import json
import logging
from groq import Groq
from app.database import supabase
from app.config import settings

# Setup Logger
logger = logging.getLogger("daksha.router")

# Initialize Groq Client using SETTINGS, not os.environ
if not settings.GROQ_API_KEY:
    logger.warning("⚠️ GROQ_API_KEY is missing in Settings. Router will default to 'general' mode.")
    groq_client = None
else:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)

class RouterService:
    @staticmethod
    async def get_loyalty_context(user_id: str) -> str:
        """
        🛡️ ALWAYS RUN: Fetches context via SQL (0 LLM Cost).
        Tables used: users, promotions, loyalty_ledger
        """
        # 1. Handle Guest/No User
        if not user_id or user_id == "guest": 
            return "User Status: Guest (No Loyalty Data)"
            
        try:
            # 2. Fetch User Loyalty Profile
            user_res = supabase.table("users")\
                .select("loyalty_tier, loyalty_points, full_name")\
                .eq("id", user_id)\
                .maybe_single()\
                .execute()
            
            # 3. Fetch Active Promotions
            promo_res = supabase.table("promotions")\
                .select("code, name, discount_value, discount_type")\
                .eq("is_active", True)\
                .limit(2)\
                .execute()
            
            context_parts = []
            
            # Format User Data
            if user_res.data:
                u = user_res.data
                context_parts.append(f"User: {u.get('full_name', 'Customer')}")
                context_parts.append(f"Loyalty: {u.get('loyalty_tier')} Tier ({u.get('loyalty_points')} pts)")
            
            # Format Promo Data
            if promo_res.data:
                promos = [f"{p['code']} ({p['name']})" for p in promo_res.data]
                context_parts.append(f"Active Offers: {', '.join(promos)}")
                
            return " | ".join(context_parts)
            
        except Exception as e:
            logger.error(f"Context Fetch Failed: {e}")
            return "User Status: Unknown (DB Error)"

    @staticmethod
    def classify_intent(message: str, context_str: str) -> dict:
        """
        🧠 FAST BRAIN: Uses Llama-3 via Groq to classify intent.
        Output: JSON Dict with 'route' and 'parameters'.
        """
        # Fallback if Groq is down/missing
        if not groq_client:
            return {"route": "synthesizer", "parameters": {}}

        system_prompt = f"""
        You are the Intent Router for 'Daksha', a Retail AI Assistant.
        
        USER CONTEXT: {context_str}
        
        YOUR TASK:
        Analyze the USER MESSAGE and map it to exactly ONE of these routes:
        
        1. "inventory": Questions about products, stock availability, finding items, or "do you have...".
           - EXTRACT: "query" (the product name), "size", "color".
           
        2. "support": Questions about past orders, order status, tracking, returns, or complaints.
           - EXTRACT: "order_id" (if present).
           
        3. "loyalty": Questions specifically about points, rewards, tier status, or how to use coupons.
        
        4. "synthesizer": General chit-chat, greetings, or if the user question is unclear.

        OUTPUT FORMAT:
        Return ONLY valid JSON. No markdown.
        Example: {{ "route": "inventory", "parameters": {{ "query": "red shoes", "size": "10" }} }}
        """

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model="llama-3.1-8b-instant", 
                response_format={"type": "json_object"},
                temperature=0.1 # Low temp for deterministic routing
            )
            
            response_content = chat_completion.choices[0].message.content
            return json.loads(response_content)

        except Exception as e:
            logger.error(f"Groq Routing Failed: {e}")
            # Fail-safe: Send to general synthesizer
            return {"route": "synthesizer", "parameters": {}}
        