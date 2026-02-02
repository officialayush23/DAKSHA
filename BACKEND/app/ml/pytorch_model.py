# app/ml/pytorch_model.py
import torch
import torch.nn as nn

class TwoTowerModel(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=32):
        super().__init__()
        
        # User Tower
        self.user_embedding = nn.Embedding(num_users + 1, embedding_dim)
        self.user_layers = nn.Sequential(
            nn.Linear(embedding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32) # Output dimension
        )

        # Item Tower
        self.item_embedding = nn.Embedding(num_items + 1, embedding_dim)
        self.item_layers = nn.Sequential(
            nn.Linear(embedding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32) # Output dimension
        )

        self.sigmoid = nn.Sigmoid()

    def forward(self, user_indices, item_indices):
        # Pass through embedding & dense layers
        user_vec = self.user_layers(self.user_embedding(user_indices))
        item_vec = self.item_layers(self.item_embedding(item_indices))
        
        # Dot Product (Interaction Score)
        score = (user_vec * item_vec).sum(dim=1)
        return self.sigmoid(score) # Return probability 0-1

    def get_user_vector(self, user_index):
        with torch.no_grad():
            return self.user_layers(self.user_embedding(user_index))

    def get_item_vector(self, item_index):
        with torch.no_grad():
            return self.item_layers(self.item_embedding(item_index))