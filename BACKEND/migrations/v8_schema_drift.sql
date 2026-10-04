-- =============================================================
-- DAKSHA v8: bring the database in line with app/models/models.py
-- (found with scripts/check_schema_drift.py). Safe to re-run.
-- =============================================================
ALTER TABLE user_addresses ADD COLUMN IF NOT EXISTS latitude  DOUBLE PRECISION;
ALTER TABLE user_addresses ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
ALTER TABLE fulfillment_attempts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;
ALTER TABLE coupon_embeddings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE coupon_embeddings ALTER COLUMN model SET DEFAULT 'nomic-embed-text-v1.5';
ALTER TABLE user_personalized_offer_embeddings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE user_personalized_offer_embeddings ALTER COLUMN model SET DEFAULT 'nomic-embed-text-v1.5';
ALTER TABLE product_price_snapshots ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid();
ALTER TABLE product_price_snapshots ADD COLUMN IF NOT EXISTS sale_price NUMERIC(10, 2);
ALTER TABLE product_price_snapshots ALTER COLUMN display_price SET DEFAULT 0;

-- policy_decisions.rule_category: allow every agent domain the gate logs
ALTER TABLE policy_decisions DROP CONSTRAINT IF EXISTS policy_decisions_rule_category_check;
ALTER TABLE policy_decisions ADD CONSTRAINT policy_decisions_rule_category_check CHECK (rule_category = ANY (ARRAY[
  'offer','return','exchange','cancellation','delivery','loyalty','payment',
  'cart','discovery','support','engagement','general']));
