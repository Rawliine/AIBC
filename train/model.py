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
        # x: shape [batch_size, seq_len, embed_dim]
        attn_out, _ = self.attn(x, x, x)
        x = x + attn_out  # skip connection
        ff_out = F.relu(self.linear_ff(x))
        x = x + ff_out
        return x

class DeeperTransformer(nn.Module):
    """
    Un Transformer plus profond pour la classification (4 classes).
    On empile plusieurs TransformerBlock.
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
        self.num_classes = num_classes
        self.num_layers = num_layers

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads)
            for _ in range(num_layers)
        ])
        self.output_head = nn.Linear(embed_dim, num_classes)

    def forward(self, x):
        """
        x: [batch_size, seq_len]
        """
        # Embedding
        embedded = self.embedding(x)  # [batch_size, seq_len, embed_dim]

        # Empiler N blocs
        for block in self.blocks:
            embedded = block(embedded)

        # Moyenne sur la séquence
        pooled = embedded.mean(dim=1)
        logits = self.output_head(pooled)
        return logits
