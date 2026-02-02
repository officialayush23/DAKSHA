# app/services/post_rank_service.py
def apply_business_rules(results):
    """
    Diversify results (Don't show 10 shirts from the same brand).
    """
    seen_brands = {}
    final_list = []
    
    for row in results:
        brand = row.brand
        if seen_brands.get(brand, 0) < 3: # Max 3 items per brand
            final_list.append(row)
            seen_brands[brand] = seen_brands.get(brand, 0) + 1
            
    return final_list