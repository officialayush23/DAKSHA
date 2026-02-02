# app/ml/model.py
import tensorflow as tf
import tensorflow_recommenders as tfrs
import numpy as np

class HybridModel(tfrs.Model):
    def __init__(self, user_model, product_model, task):
        super().__init__()
        self.user_model = user_model
        self.product_model = product_model
        self.task = task

    def compute_loss(self, features, training=False):
        user_embeddings = self.user_model(features["user_id"])
        positive_product_embeddings = self.product_model(features["product_id"])

        return self.task(user_embeddings, positive_product_embeddings)

def build_model(unique_user_ids, unique_product_ids, embedding_dimension=32):
    """
    Builds a Two-Tower architecture.
    """
    # 1. User Tower
    user_model = tf.keras.Sequential([
        tf.keras.layers.StringLookup(
            vocabulary=unique_user_ids, mask_token=None),
        tf.keras.layers.Embedding(len(unique_user_ids) + 1, embedding_dimension)
    ])

    # 2. Product Tower
    product_model = tf.keras.Sequential([
        tf.keras.layers.StringLookup(
            vocabulary=unique_product_ids, mask_token=None),
        tf.keras.layers.Embedding(len(unique_product_ids) + 1, embedding_dimension)
    ])

    # 3. Retrieval Task
    task = tfrs.tasks.Retrieval(
        metrics=tfrs.metrics.FactorizedTopK(
            candidates=tf.data.Dataset.from_tensor_slices(unique_product_ids).batch(128).map(product_model)
        )
    )

    return HybridModel(user_model, product_model, task)