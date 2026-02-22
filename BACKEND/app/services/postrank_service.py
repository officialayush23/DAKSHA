# app/services/post_rank_service.py
def apply_business_rules(results):
    """
    Phase 3: POST-RANK. Diversifies feed to prevent showing 10 items from the same brand.
    Expects a list of dictionaries (from ranking_service).
    """
    seen_brands = {}
    final_list = []
    
    for r in results:
        brand = r.get("brand") or "Unknown"
        
        if seen_brands.get(brand, 0) < 3: # Max 3 items per brand in a row
            final_list.append(r)
            seen_brands[brand] = seen_brands.get(brand, 0) + 1
            
    return final_list