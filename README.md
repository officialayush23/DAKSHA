# DAKSHA 
EY TECHATHON 6.0


 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000




 onClick={() => {
  trackEvent("click_product", { product_id: product.id });
  navigate(`/products/${product.id}`);
}}




trackEvent("search", {
  query: searchText,
  filters: appliedFilters,
});



trackAddToCart(product, qty);



trackEvent("checkout_start", { cart_total, items });
