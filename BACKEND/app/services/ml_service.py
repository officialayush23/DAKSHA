# app/services/ml_service.py
import torch
import torch.nn as nn
import torch.optim as optim
import math
import random
import time  # For timing the training
import logging
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Event
from app.enums.db_enums import EntityTypeEnum, EventTypeEnum
from app.ml.pytorch_model import TwoTowerModel

# Setup standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global In-Memory Cache
TRAINED_MODEL = None
USER_MAP = {} 
ITEM_MAP = {} 
REVERSE_ITEM_MAP = {}

REWARD_MAP = {
    EventTypeEnum.product_view: 0.1,
    EventTypeEnum.search: 0.2,
    EventTypeEnum.add_to_cart: 0.6,
    EventTypeEnum.order_placed: 1.0, 
}

def decay_weight(event_time, tau_days=30):
    if not event_time: return 0.5
    delta_days = (datetime.now(event_time.tzinfo) - event_time).days
    return math.exp(-max(0, delta_days) / tau_days)

def train_collaborative_model(db: Session):
    global TRAINED_MODEL, USER_MAP, ITEM_MAP, REVERSE_ITEM_MAP
    start_time = time.time()

    logger.info("🚀 Starting Collaborative Model Training...")

    # 1. Fetch Data
    events = db.query(Event).filter(
    Event.user_id.isnot(None),
    Event.entity_type == EntityTypeEnum.product_variant,
).all()

    if not events:
        logger.warning("⚠️ No interaction data found in 'events' table. Training aborted.")
        return {"status": "No data to train"}

    # 2. Build Mappings
    user_ids = sorted(list(set([str(e.user_id) for e in events])))
    item_ids = sorted(list(set([str(e.entity_id) for e in events])))
    
    USER_MAP = {uid: i for i, uid in enumerate(user_ids)}
    ITEM_MAP = {iid: i for i, iid in enumerate(item_ids)}
    REVERSE_ITEM_MAP = {i: iid for iid, i in ITEM_MAP.items()}

    logger.info(f"📊 Dataset Stats: {len(user_ids)} Users, {len(item_ids)} Items, {len(events)} Interactions")

    # 3. Build Training Set
    X_users, X_items, y_labels = [], [], []

    for e in events:
        if str(e.user_id) in USER_MAP and str(e.entity_id) in ITEM_MAP:
            base_reward = REWARD_MAP.get(e.event_type, 0.1)
            time_factor = decay_weight(e.created_at)
            label = min(1.0, base_reward * time_factor)

            X_users.append(USER_MAP[str(e.user_id)])
            X_items.append(ITEM_MAP[str(e.entity_id)])
            y_labels.append(label)

    # Negative Sampling
    num_negatives = len(X_users)
    all_item_indices = list(ITEM_MAP.values())
    all_user_indices = list(USER_MAP.values())
    for _ in range(num_negatives):
        X_users.append(random.choice(all_user_indices))
        X_items.append(random.choice(all_item_indices))
        y_labels.append(0.0)

    # 4. Convert to Tensors
    X_users_t = torch.LongTensor(X_users)
    X_items_t = torch.LongTensor(X_items)
    y_labels_t = torch.FloatTensor(y_labels)

    # 5. Train
    model = TwoTowerModel(len(USER_MAP), len(ITEM_MAP))
    criterion = nn.MSELoss() 
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    model.train()
    epochs = 10
    logger.info(f"🧠 Training for {epochs} epochs...")

    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_users_t, X_items_t)
        loss = criterion(outputs, y_labels_t)
        loss.backward()
        optimizer.step()
        
        # Log loss every 2 epochs
        if epoch % 2 == 0:
            logger.info(f"   🔹 Epoch {epoch}/{epochs} | Loss: {loss.item():.4f}")

    TRAINED_MODEL = model
    model.eval()

    total_duration = time.time() - start_time
    logger.info(f"✅ Training Complete! Total time: {total_duration:.2f} seconds")
    
    return {
        "status": "Trained", 
        "samples": len(y_labels), 
        "duration_sec": round(total_duration, 2)
    }

def get_collaborative_candidates(user_uuid: str, k=200):
    if TRAINED_MODEL is None or str(user_uuid) not in USER_MAP:
        return []

    user_idx = torch.LongTensor([USER_MAP[str(user_uuid)]])
    user_vec = TRAINED_MODEL.get_user_vector(user_idx)
    all_items = torch.arange(len(ITEM_MAP))
    item_vecs = TRAINED_MODEL.get_item_vector(all_items)
    
    scores = torch.matmul(user_vec, item_vecs.T).squeeze()
    _, indices = torch.topk(scores, k=min(k, len(ITEM_MAP)))
    
    return [REVERSE_ITEM_MAP[idx.item()] for idx in indices]


from app.models.models import OrderItem, ProductAffinity

def build_affinity_graph(db: Session):
    """
    Populates the 'Often Bought Together' graph (product_affinities table).
    Run this as a background task.
    """
    logger.info("🕸️ Building Product Affinity Graph...")
    
    # 1. Clear old Global affinities
    db.query(ProductAffinity).filter(ProductAffinity.context_scope == 'global').delete()
    
    # 2. Compute Co-occurrences via Self-Join on OrderItems
    # "Find pairs of items appearing in the same Order"
    sql = text("""
        INSERT INTO product_affinities (product_variant_id_a, product_variant_id_b, score, context_scope)
        SELECT 
            t1.product_variant_id, 
            t2.product_variant_id, 
            COUNT(*) / (SELECT COUNT(*) FROM orders)::numeric as score, -- Normalize score
            'global'
        FROM order_items t1
        JOIN order_items t2 ON t1.order_id = t2.order_id
        WHERE t1.product_variant_id != t2.product_variant_id
        GROUP BY t1.product_variant_id, t2.product_variant_id
        HAVING COUNT(*) > 1 -- Only significant pairs
        ORDER BY score DESC;
    """)
    
    db.execute(sql)
    db.commit()
    logger.info("✅ Affinity Graph Updated.")
    
    
    
def nightly_ml_jobs(db: Session):
    from app.services.ml_service import train_collaborative_model, build_affinity_graph

    train_collaborative_model(db)
    build_affinity_graph(db)

