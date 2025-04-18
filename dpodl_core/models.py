import torch
import torch.nn as nn
import torch.nn.functional as F

class TransformerBlock(nn.Module):
    """
    Un bloc Transformer simplifié :
      - MultiheadAttention
      - skip connection
      - feed-forward (linear) + skip
    """
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.linear_ff = nn.Linear(embed_dim, embed_dim)

    def forward(self, x):
        # x: [batch_size, seq_len, embed_dim]
        attn_out, _ = self.attn(x, x, x)
        x = x + attn_out  # skip connection
        ff_out = F.relu(self.linear_ff(x))
        x = x + ff_out
        return x

class DeeperTransformer(nn.Module):
    """
    Un Transformer plus profond pour la classification.
    On empile plusieurs TransformerBlock (num_layers).
    """
    def __init__(self,
                 vocab_size=30522,
                 embed_dim=256,
                 seq_len=128,
                 num_heads=8,
                 num_layers=6,
                 num_classes=4):
        super().__init__()
        self.seq_len = seq_len
        self.embed_dim = embed_dim
        self.num_layers = num_layers

        # Embedding initial, type BERT
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # Empiler N blocs identiques
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads)
            for _ in range(num_layers)
        ])

        # Projection finale -> classes
        self.output_head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        """
        x: [batch_size, seq_len] -> tokens
        """
        embedded = self.embedding(x)  # [batch_size, seq_len, embed_dim]

        for block in self.blocks:
            embedded = block(embedded)

        # Average Pool
        pooled = embedded.mean(dim=1)  # [batch_size, embed_dim]
        logits = self.output_head(pooled)
        return logits
