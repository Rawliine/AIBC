# train/model.py

import torch
import torch.nn as nn
import torch.nn.functional as F

class SimpleTransformer(nn.Module):
    """
    Mini-Transformeur pour classification (4 classes),
    1 couche de MultiheadAttention, feed-forward, skip connection.
    """

    def __init__(self, vocab_size=20000, embed_dim=128, seq_len=32, num_heads=2, num_classes=4):
        super().__init__()
        self.seq_len = seq_len
        self.embed_dim = embed_dim
        self.num_classes = num_classes

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.attention = nn.MultiheadAttention(embed_dim, num_heads=num_heads, batch_first=True)
        self.linear_ff = nn.Linear(embed_dim, embed_dim)
        self.output_head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        """
        x: [batch_size, seq_len] (tokens)
        """
        # [batch_size, seq_len, embed_dim]
        embedded = self.embedding(x)

        # Self-attention
        attn_out, _ = self.attention(embedded, embedded, embedded)
        x_attn = embedded + attn_out  # skip connection

        # Feed-forward
        ff = F.relu(self.linear_ff(x_attn))
        # average pooling sur la seq
        pooled = ff.mean(dim=1)
        logits = self.output_head(pooled)  # shape [batch_size, num_classes]
        return logits
