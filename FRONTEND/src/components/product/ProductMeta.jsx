//  src/components/product/ProductMeta.jsx

export default function ProductMeta({ product, price }) {
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-widest text-muted-foreground">
        {product.gender}
      </p>

      <h1 className="text-2xl md:text-3xl font-semibold">
        {product.name}
      </h1>

      <p className="text-xl font-bold">
        ₹{price}
      </p>

      {product.description && (
        <p className="text-sm text-muted-foreground pt-2">
          {product.description}
        </p>
      )}
    </div>
  );
}
