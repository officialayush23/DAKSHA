# app/services/personalized_offer_Service.py
def compute_personalized_offers(db, user_id, recommended_variants):
    offers = []

    for variant in recommended_variants:
        discount = 0
        reason = None

        # High intent → higher discount
        if variant["debug_scores"]["intent"] > 0.75:
            discount = 15
            reason = "High intent match"

        # Loyalty tier boost
        user = db.query(User).get(user_id)
        if user.loyalty_tier == "Gold":
            discount += 5
            reason = (reason or "") + " + Gold member bonus"

        if discount > 0:
            offers.append({
                "variant_id": variant["variant_id"],
                "discount_percent": min(discount, 30),
                "reason": reason
            })

    return offers
