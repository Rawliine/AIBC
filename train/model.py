# train/model.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class SimpleTransformer(nn.Module):
    """
    Un mini-Transformeur très simplifié :
    - Embedding
    - Self-Attention + feed-forward
    - Projection finale
    """

    def __init__(self, vocab_size=1000, embed_dim=128, seq_len=32):
        super().__init__()
        self.seq_len = seq_len
        self.embed_dim = embed_dim

        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.attention = nn.MultiheadAttention(embed_dim, num_heads=2, batch_first=True)
        self.linear_ff = nn.Linear(embed_dim, embed_dim)
        self.output_head = nn.Linear(embed_dim, 1)  # ex: sortie binaire

    def forward(self, x):
        """
        x: [batch_size, seq_len] contenant des indices (tokens)
        """
        # [batch_size, seq_len, embed_dim]
        embedded = self.embedding(x)

        # Self-attention
        attn_out, _ = self.attention(embedded, embedded, embedded)
        # Ajout + normalisation (simplifié ici)
        x_attn = embedded + attn_out

        # Passage feed-forward
        ff = F.relu(self.linear_ff(x_attn))

        # Output (on agrège un peu le batch)
        # On fait, par ex., la moyenne sur la séquence, puis on projette
        pooled = ff.mean(dim=1)  # [batch_size, embed_dim]
        logits = self.output_head(pooled)  # [batch_size, 1]

        return logits.squeeze(-1)
