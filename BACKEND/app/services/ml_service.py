# app/services/ml_service.py
import torch
import torch.nn as nn
import torch.optim as optim
import math
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Event
from app.enums.db_enums import EventTypeEnum
from app.ml.pytorch_model import TwoTowerModel

# Global In-Memory Cache (Use Redis/FAISS in prod)
TRAINED_MODEL = None
USER_MAP = {} 
ITEM_MAP = {} 
REVERSE_ITEM_MAP = {}

# REWARD CONFIGURATION
REWARD_MAP = {
    EventTypeEnum.product_view: 0.1,
    EventTypeEnum.search: 0.2,
    EventTypeEnum.add_to_cart: 0.6,
    EventTypeEnum.order_placed: 1.0, 
}

def decay_weight(event_time, tau_days=30):
    """
    Time decay function: Newer events have higher weight.
    Formula: e^(-delta_days / tau)
    """
    if not event_time: return 0.5
    # Ensure event_time is naive or consistent timezone
    delta_days = (datetime.now(event_time.tzinfo) - event_time).days
    return math.exp(-max(0, delta_days) / tau_days)

def train_collaborative_model(db: Session):
    global TRAINED_MODEL, USER_MAP, ITEM_MAP, REVERSE_ITEM_MAP

    # 1. Fetch Interaction Data
    # Only events where a user interacted with a specific product
    events = db.query(Event).filter(Event.entity_id.isnot(None)).all()

    if not events: return {"status": "No data to train"}

    # 2. Build Index Mappings
    user_ids = sorted(list(set([str(e.user_id) for e in events])))
    item_ids = sorted(list(set([str(e.entity_id) for e in events])))
    
    USER_MAP = {uid: i for i, uid in enumerate(user_ids)}
    ITEM_MAP = {iid: i for i, iid in enumerate(item_ids)}
    REVERSE_ITEM_MAP = {i: iid for iid, i in ITEM_MAP.items()}

    # 3. Build Training Set
    X_users, X_items, y_labels = [], [], []

    # A. Positive Samples (Weighted)
    for e in events:
        if str(e.user_id) in USER_MAP and str(e.entity_id) in ITEM_MAP:
            base_reward = REWARD_MAP.get(e.event_type, 0.1)
            time_factor = decay_weight(e.created_at)
            
            # Final Label: 0.0 to 1.0 (How "good" was this interaction?)
            label = min(1.0, base_reward * time_factor)

            X_users.append(USER_MAP[str(e.user_id)])
            X_items.append(ITEM_MAP[str(e.entity_id)])
            y_labels.append(label)

    # B. Negative Sampling (Crucial for Two-Tower)
    # Randomly assign items user didn't interact with as 0.0
    num_negatives = len(X_users)
    all_item_indices = list(ITEM_MAP.values())
    all_user_indices = list(USER_MAP.values())
    
    for _ in range(num_negatives):
        u = random.choice(all_user_indices)
        i = random.choice(all_item_indices)
        X_users.append(u)
        X_items.append(i)
        y_labels.append(0.0) # Explicit Negative

    # 4. Convert to Tensors
    X_users_t = torch.LongTensor(X_users)
    X_items_t = torch.LongTensor(X_items)
    y_labels_t = torch.FloatTensor(y_labels)

    # 5. Train
    model = TwoTowerModel(len(USER_MAP), len(ITEM_MAP))
    # MSE is better for regression (weighted labels), BCELoss for pure binary 0/1
    criterion = nn.MSELoss() 
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    model.train()
    for _ in range(10): # 10 Epochs
        optimizer.zero_grad()
        outputs = model(X_users_t, X_items_t)
        loss = criterion(outputs, y_labels_t)
        loss.backward()
        optimizer.step()

    TRAINED_MODEL = model
    model.eval()
    return {"status": "Trained", "samples": len(y_labels)}

def get_collaborative_candidates(user_uuid: str, k=200):
    """
    Inference: Returns top-K item UUIDs for a user.
    """
    if TRAINED_MODEL is None or str(user_uuid) not in USER_MAP:
        return []

    user_idx = torch.LongTensor([USER_MAP[str(user_uuid)]])
    
    # User Vector
    user_vec = TRAINED_MODEL.get_user_vector(user_idx)
    
    # Score against ALL items
    all_items = torch.arange(len(ITEM_MAP))
    item_vecs = TRAINED_MODEL.get_item_vector(all_items)
    
    # Dot Product
    scores = torch.matmul(user_vec, item_vecs.T).squeeze()
    
    # Top K
    _, indices = torch.topk(scores, k=min(k, len(ITEM_MAP)))
    
    return [REVERSE_ITEM_MAP[idx.item()] for idx in indices]