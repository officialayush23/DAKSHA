# app/services/ml_service.py
# import tensorflow as tf
# import numpy as np
# from sqlalchemy.orm import Session
# from app.models.models import Event, User, ProductVariant
# from app.enums.db_enums import EventTypeEnum
# from app.ml.model import build_model
# import os

# # Global cache for the loaded model
# TRAINED_MODEL = None
# INDEX = None

# def train_collaborative_model(db: Session):
#     """
#     Fetches interaction data (Views, Carts, Purchases) and trains the TF model.
#     """
#     global TRAINED_MODEL, INDEX
    
#     # 1. Fetch Data (Implicit Feedback)
#     # We treat 'purchase' as strong signal, 'view' as weak. 
#     # For retrieval, we just need (user, item) pairs that are "positive".
#     results = db.query(Event.user_id, Event.entity_id).filter(
#         Event.event_type.in_([EventTypeEnum.add_to_cart, EventTypeEnum.order_placed]),
#         Event.entity_id.isnot(None)
#     ).all()

#     if not results:
#         return {"status": "No data to train"}

#     # Convert UUIDs to strings for TF
#     user_ids = [str(r.user_id) for r in results]
#     product_ids = [str(r.entity_id) for r in results]

#     # 2. Prepare Datasets
#     interactions_ds = tf.data.Dataset.from_tensor_slices({
#         "user_id": user_ids,
#         "product_id": product_ids
#     })

#     unique_user_ids = np.unique(user_ids)
#     unique_product_ids = np.unique(product_ids)

#     # 3. Build & Train
#     model = build_model(unique_user_ids, unique_product_ids)
#     model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))
    
#     # Quick training (1 epoch for demo speed, increase for prod)
#     model.fit(interactions_ds.batch(4096), epochs=3, verbose=0)

#     # 4. Create Retrieval Index (BruteForce for accuracy, ScaNN for speed)
#     # We pre-calculate all product embeddings so inference is fast.
#     index = tfrs.layers.factorized_top_k.BruteForce(model.user_model)
    
#     # Get all candidate product IDs from DB to ensure we recommend valid items
#     all_products = db.query(ProductVariant.id).all()
#     all_product_ids_str = [str(p.id) for p in all_products]
    
#     index.index_from_dataset(
#         tf.data.Dataset.from_tensor_slices(all_product_ids_str).batch(100).map(lambda x: (x, model.product_model(x)))
#     )

#     TRAINED_MODEL = model
#     INDEX = index
#     return {"status": "Trained", "users": len(unique_user_ids)}

# def get_collaborative_candidates(user_id: str, k=50):
#     """
#     Returns top K product IDs from the TF model.
#     """
#     if INDEX is None:
#         return [] # Cold start / Model not ready
    
#     # Run Inference
#     _, titles = INDEX(tf.constant([str(user_id)]))
    
#     # Convert tensors back to UUID strings
#     return [t.decode('utf-8') for t in titles[0, :k].numpy()]

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sqlalchemy.orm import Session
from app.models.models import Event, ProductVariant
from app.enums.db_enums import EventTypeEnum
from app.ml.pytorch_model import TwoTowerModel

# In-memory storage for MVP (Use Redis/FAISS in prod)
TRAINED_MODEL = None
USER_MAP = {} # UUID -> Int ID
ITEM_MAP = {} # UUID -> Int ID
REVERSE_ITEM_MAP = {} # Int ID -> UUID

def train_collaborative_model(db: Session):
    global TRAINED_MODEL, USER_MAP, ITEM_MAP, REVERSE_ITEM_MAP

    # 1. Fetch Interaction Data
    events = db.query(Event).filter(
        Event.event_type.in_([EventTypeEnum.add_to_cart, EventTypeEnum.order_placed]),
        Event.entity_id.isnot(None)
    ).all()

    if not events: return {"status": "No data"}

    # 2. Build Mappings (UUID <-> Integer Index)
    user_ids = sorted(list(set([str(e.user_id) for e in events])))
    item_ids = sorted(list(set([str(e.entity_id) for e in events])))
    
    USER_MAP = {uid: i for i, uid in enumerate(user_ids)}
    ITEM_MAP = {iid: i for i, iid in enumerate(item_ids)}
    REVERSE_ITEM_MAP = {i: iid for iid, i in ITEM_MAP.items()}

    # 3. Prepare Tensors
    X_users = []
    X_items = []
    y_labels = []

    # Positive Samples
    for e in events:
        X_users.append(USER_MAP[str(e.user_id)])
        X_items.append(ITEM_MAP[str(e.entity_id)])
        y_labels.append(1.0)
    
    # Negative Sampling (Randomly assign items user didn't buy)
    # 1:1 Ratio for simplicity
    import random
    for _ in range(len(events)):
        u = random.choice(list(USER_MAP.values()))
        i = random.choice(list(ITEM_MAP.values()))
        X_users.append(u)
        X_items.append(i)
        y_labels.append(0.0) # Label 0 for negative

    X_users = torch.LongTensor(X_users)
    X_items = torch.LongTensor(X_items)
    y_labels = torch.FloatTensor(y_labels)

    # 4. Initialize & Train
    model = TwoTowerModel(len(USER_MAP), len(ITEM_MAP))
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    model.train()
    for epoch in range(5): # Fast training
        optimizer.zero_grad()
        outputs = model(X_users, X_items)
        loss = criterion(outputs, y_labels)
        loss.backward()
        optimizer.step()

    TRAINED_MODEL = model
    model.eval()
    return {"status": "Trained", "users": len(USER_MAP), "items": len(ITEM_MAP)}

def get_collaborative_candidates(user_uuid: str, k=50):
    """
    Returns top-K item UUIDs for a user based on dot-product similarity.
    """
    if TRAINED_MODEL is None or str(user_uuid) not in USER_MAP:
        return []

    user_idx = torch.LongTensor([USER_MAP[str(user_uuid)]])
    
    # Get user vector
    user_vec = TRAINED_MODEL.get_user_vector(user_idx) # Shape: [1, 32]
    
    # Calculate scores against ALL items (Brute-force is fine for <10k items)
    # In prod, index `item_vectors` into FAISS
    all_items_indices = torch.arange(len(ITEM_MAP))
    item_vecs = TRAINED_MODEL.get_item_vector(all_items_indices) # Shape: [N, 32]
    
    # Dot product
    scores = torch.matmul(user_vec, item_vecs.T).squeeze()
    
    # Get Top K
    top_k_scores, top_k_indices = torch.topk(scores, k=min(k, len(ITEM_MAP)))
    
    # Convert back to UUIDs
    return [REVERSE_ITEM_MAP[idx.item()] for idx in top_k_indices]