# # app/services/agent_service.py
# from google import genai
# from groq import Groq
# from sqlalchemy.orm import Session
# from app.core.config import settings
# from app.agents.tools import AgentTools
# from app.models.models import ConversationSummary, UserSession 

# # Initialize Clients
# genai.Client(api_key=settings.GEMINI_API_KEY)
# groq_client = Groq(api_key=settings.GROQ_API_KEY)

# SYSTEM_PROMPT = """
# You are the Aditya Birla Fashion Concierge name of the brand is "DAKSHA", an elite sales associate for brands like Louis Philippe, Van Heusen, and Allen Solly.
# Your goal is to provide a seamless, consultative shopping experience.

# STRATEGY:
# 1. KIOSK MODE: If the user is at a Kiosk, they are IN-STORE. Prioritize 'find_nearest_stores' and 'check_local_store_stock' for the CURRENT store location.
# 2. CONSULTATIVE: If a user is searching, ask about the occasion (Wedding, Office, Casual).
# 3. TRANSACTIONAL: If a user wants to buy, guide them to 'add_item_to_cart' and then 'view_my_cart'.
# 4. PERSUASION: If the user mentions a failed payment, offer to check 'get_available_offers' to see if a discount makes the purchase easier.
# 5. OMNICHANNEL: Acknowledge past interactions if context is provided.
# 6. EXPLAIN SUGGESTIONS: When suggesting products, use the user's preference summary to explain why. 
#    Example: "Based on your interest in linen fabrics, I recommend..."
# 7. MULTI-AGENT ORCHESTRATION: If stock is low in the warehouse, check local stores, retry checkout if fails on payment.
# 8. SUPPORT MODE: You can also login complaints and solve Daksha related queries , like the type of products.
# 9. INFO AGNET: Provide info about orders, cart_items , delivery status , cards , addresses , etc.

# STRICT LIMIT: Do not delete accounts. Do not process actual payments (redirect to checkout).
# """
# async def run_omnichannel_agent(db: Session, user_id, session_id, message, channel):
#     # 1. Fetch Context & Summary
#     summary = db.query(ConversationSummary).filter_by(session_id=session_id).first()
    
#     # 2. FAST-PASS: Intent Classification with Groq (Llama 3)
#     # This prevents 'model drift' and keeps the agent focused.
#     routing_prompt = f"""
#     Analyze the user message: "{message}"
#     Classify into ONE category: 
#     - RECOMMEND (Searching/Fashion advice)
#     - TRANSACTION (Cart/Checkout/Address)
#     - SUPPORT (Orders/Complaints)
#     - INVENTORY (Store locations/Stock)
#     - OTHER (General chat)
    
#     Return ONLY the category name.
#     """
    
#     intent_classification = groq_client.chat.completions.create(
#         model="llama3-70b-8192",
#         messages=[{"role": "user", "content": routing_prompt}],
#         temperature=0, # Strict classification
#     )
#     detected_intent = intent_classification.choices[0].message.content.strip()

#     # 3. Context Injection (Kiosk / Channel / Summary)
#     context_prefix = f"[Channel: {channel}] [Detected Intent: {detected_intent}] "
#     if summary:
#         context_prefix += f"[Context Summary: {summary.summary_text}] "

#     # 4. Tool-Enabled Reasoning (Gemini 2.5 Flash)
#     tools = AgentTools(db, user_id, session_id)
    
#     # We pass the detected_intent into the prompt to guide Gemini's tool selection
#     model = genai.GenerativeModel(
#         model_name='gemini-2.5-flash',
#         system_instruction=SYSTEM_PROMPT,
#         tools=[
#             tools.get_fashion_recommendations,
#             tools.find_nearest_stores,
#             tools.view_my_cart,
#             tools.add_item_to_cart,
#             tools.update_shipping_address,
#             tools.list_my_orders,
#             tools.get_order_details,
#             tools.list_my_complaints,
#             tools.raise_new_complaint,
#             tools.check_local_store_stock,
#             tools.get_available_offers
#         ]
#     )

#     chat = model.start_chat(enable_automatic_function_calling=True)
    
#     # If Groq detected a simple intent, we can prioritize that path
#     response = chat.send_message(f"{context_prefix} User: {message}")
    
#     return response.text