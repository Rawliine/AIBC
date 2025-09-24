import pytest
import torch
import os
from unittest.mock import patch, MagicMock, mock_open

# Adjust the import path based on your project structure
from dpodl_core.utils import save_checkpoint, load_checkpoint, collate_batch
from dpodl_core.models import DeeperTransformer # Use a simple model for testing state dict

# --- Fixtures ---

@pytest.fixture
def mock_model():
    """Provides a simple mock model with a state_dict."""
    model = DeeperTransformer(vocab_size=100, embed_dim=16, seq_len=8, num_heads=2, num_layers=1, num_classes=2)
    # Add some dummy state
    model.embedding.weight.data.fill_(0.1)
    return model

@pytest.fixture
def mock_optimizer(mock_model):
    """Provides a mock optimizer with a state_dict."""
    optimizer = torch.optim.Adam(mock_model.parameters(), lr=1e-3)
    # Add some dummy state (e.g., after one step)
    optimizer.state = {'step': torch.tensor(1), 'exp_avg': {}, 'exp_avg_sq': {}}
    return optimizer

@pytest.fixture
def sample_batch_data():
    """Provides sample batch data similar to HF datasets format."""
    return [
        {'input_ids': [10, 20, 30, 0], 'label': 1},
        {'input_ids': [40, 50], 'label': 0},
        {'input_ids': [60, 70, 80, 90, 100], 'label': 1} # Longer sequence
    ]

# --- Test Functions ---

@patch('dpodl_core.utils.torch.save')
@patch('dpodl_core.utils.ipfshttpclient.connect')
@patch('builtins.open', new_callable=mock_open)
def test_save_checkpoint(mock_file_open, mock_ipfs_connect, mock_torch_save, mock_model, mock_optimizer):
    """Tests the save_checkpoint function including IPFS upload."""
    epoch = 5
    loss = 0.123
    checkpoint_path = "test_checkpoint.pt"
    expected_cid = "QmTestCid"

    # Configure the mock IPFS client
    mock_client = MagicMock()
    mock_client.add.return_value = {'Hash': expected_cid}
    mock_ipfs_connect.return_value = mock_client

    # Call the function
    cid = save_checkpoint(epoch, mock_model, mock_optimizer, loss, checkpoint_path)

    # Assert torch.save was called correctly
    mock_torch_save.assert_called_once()
    args, _ = mock_torch_save.call_args
    saved_data = args[0]
    save_path = args[1]
    assert save_path == checkpoint_path
    assert saved_data['epoch'] == epoch
    assert saved_data['loss'] == loss
    assert 'model_state_dict' in saved_data
    assert 'optimizer_state_dict' in saved_data

    # Assert IPFS connect and add were called
    mock_ipfs_connect.assert_called_once_with('/ip4/127.0.0.1/tcp/5001', timeout=5)
    mock_client.add.assert_called_once_with(checkpoint_path)

    # Assert CID file was written to
    mock_file_open.assert_called_once_with('checkpoint_cids.txt', 'a')
    mock_file_handle = mock_file_open()
    mock_file_handle.write.assert_called_once_with(f"{epoch},{expected_cid},{checkpoint_path}\n")

    # Assert the correct CID was returned
    assert cid == expected_cid


@patch('dpodl_core.utils.os.path.isfile')
@patch('dpodl_core.utils.torch.load')
def test_load_checkpoint_exists(mock_torch_load, mock_isfile, mock_model, mock_optimizer):
    """Tests loading an existing checkpoint."""
    checkpoint_path = "test_checkpoint.pt"
    expected_epoch = 5
    expected_loss = 0.123
    mock_model_state = mock_model.state_dict()
    mock_optimizer_state = mock_optimizer.state_dict()

    # Configure mocks
    mock_isfile.return_value = True
    mock_torch_load.return_value = {
        "epoch": expected_epoch,
        "model_state_dict": mock_model_state,
        "optimizer_state_dict": mock_optimizer_state,
        "loss": expected_loss
    }

    # Create fresh model/optimizer instances to load into
    load_model = DeeperTransformer(vocab_size=100, embed_dim=16, seq_len=8, num_heads=2, num_layers=1, num_classes=2)
    load_optimizer = torch.optim.Adam(load_model.parameters())

    # Call the function
    epoch, loss, dpodl_state = load_checkpoint(checkpoint_path, load_model, load_optimizer)

    # Assertions
    mock_isfile.assert_called_once_with(checkpoint_path)
    mock_torch_load.assert_called_once_with(checkpoint_path, map_location="cpu", weights_only=True)
    assert epoch == expected_epoch
    assert loss == expected_loss
    # Check if state dicts were loaded (simple check)
    assert torch.equal(load_model.embedding.weight, mock_model.embedding.weight)
    # Optimizer state loading is harder to verify precisely without internal knowledge,
    # but we check if load_state_dict was called implicitly by torch.load


@patch('dpodl_core.utils.os.path.isfile')
@patch('dpodl_core.utils.torch.load')
def test_load_checkpoint_secure_fallback(mock_torch_load, mock_isfile, mock_model, mock_optimizer):
    """Tests loading checkpoint with fallback from weights_only=True to weights_only=False."""
    checkpoint_path = "test_checkpoint.pt"
    expected_epoch = 3
    expected_loss = 0.456
    mock_model_state = mock_model.state_dict()
    mock_optimizer_state = mock_optimizer.state_dict()
    
    # Configure mocks - first call fails, second succeeds
    mock_isfile.return_value = True
    mock_torch_load.side_effect = [
        Exception("weights_only=True failed"),  # First call fails
        {  # Second call succeeds
            "epoch": expected_epoch,
            "model_state_dict": mock_model_state,
            "optimizer_state_dict": mock_optimizer_state,
            "loss": expected_loss
        }
    ]
    
    # Create fresh model/optimizer instances to load into
    load_model = DeeperTransformer(vocab_size=100, embed_dim=16, seq_len=8, num_heads=2, num_layers=1, num_classes=2)
    load_optimizer = torch.optim.Adam(load_model.parameters())
    
    # Call the function
    epoch, loss, dpodl_state = load_checkpoint(checkpoint_path, load_model, load_optimizer)
    
    # Assertions
    mock_isfile.assert_called_once_with(checkpoint_path)
    # Should be called twice: first with weights_only=True, then with weights_only=False
    assert mock_torch_load.call_count == 2
    mock_torch_load.assert_any_call(checkpoint_path, map_location="cpu", weights_only=True)
    mock_torch_load.assert_any_call(checkpoint_path, map_location="cpu", weights_only=False)
    assert epoch == expected_epoch
    assert loss == expected_loss


@patch('dpodl_core.utils.os.path.isfile')
def test_load_checkpoint_not_exists(mock_isfile, mock_model, mock_optimizer):
    """Tests loading when the checkpoint file doesn't exist."""
    checkpoint_path = "non_existent_checkpoint.pt"
    mock_isfile.return_value = False

    # Create fresh model/optimizer instances
    load_model = DeeperTransformer(vocab_size=100, embed_dim=16, seq_len=8, num_heads=2, num_layers=1, num_classes=2)
    load_optimizer = torch.optim.Adam(load_model.parameters())

    # Call the function
    epoch, loss, dpodl_state = load_checkpoint(checkpoint_path, load_model, load_optimizer)

    # Assertions
    mock_isfile.assert_called_once_with(checkpoint_path)
    assert epoch == 0
    assert loss == float("inf")


def test_collate_batch(sample_batch_data):
    """Tests the collate_batch function for padding and truncation."""
    seq_len = 4 # Define a sequence length for the test

    texts_t, labels_t = collate_batch(sample_batch_data, seq_len=seq_len)

    # Expected tensors
    # Seq len 4:
    # [10, 20, 30, 0] -> [10, 20, 30, 0] (label 1)
    # [40, 50]        -> [40, 50, 0, 0]  (label 0)
    # [60, 70, 80, 90, 100] -> [60, 70, 80, 90] (label 1, truncated)
    expected_texts = torch.tensor([
        [10, 20, 30, 0],
        [40, 50, 0, 0],
        [60, 70, 80, 90]
    ], dtype=torch.long)
    expected_labels = torch.tensor([1, 0, 1], dtype=torch.long)

    assert torch.equal(texts_t, expected_texts)
    assert torch.equal(labels_t, expected_labels)
    assert texts_t.shape == (3, seq_len) # Batch size 3, sequence length 4
    assert labels_t.shape == (3,)        # Batch size 3

def test_collate_batch_longer_seq(sample_batch_data):
    """Tests collate_batch with a longer sequence length."""
    seq_len = 6

    texts_t, labels_t = collate_batch(sample_batch_data, seq_len=seq_len)

    # Expected tensors
    # Seq len 6:
    # [10, 20, 30, 0] -> [10, 20, 30, 0, 0, 0] (label 1)
    # [40, 50]        -> [40, 50, 0, 0, 0, 0]  (label 0)
    # [60, 70, 80, 90, 100] -> [60, 70, 80, 90, 100, 0] (label 1)
    expected_texts = torch.tensor([
        [10, 20, 30, 0, 0, 0],
        [40, 50, 0, 0, 0, 0],
        [60, 70, 80, 90, 100, 0]
    ], dtype=torch.long)
    expected_labels = torch.tensor([1, 0, 1], dtype=torch.long)

    assert torch.equal(texts_t, expected_texts)
    assert torch.equal(labels_t, expected_labels)
    assert texts_t.shape == (3, seq_len)
    assert labels_t.shape == (3,)
