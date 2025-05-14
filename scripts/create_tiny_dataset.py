import os
from datasets import load_dataset
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tiny_dataset():
    output_base_dir = "./data/ag_news_tiny"
    num_train_samples = 200
    num_test_samples = 50

    logger.info(f"Attempting to create tiny dataset at {output_base_dir}")
    logger.info(f"Number of train samples: {num_train_samples}")
    logger.info(f"Number of test samples: {num_test_samples}")

    try:
        # Create directories if they don't exist
        os.makedirs(output_base_dir, exist_ok=True)
        logger.info(f"Ensured directory exists: {output_base_dir}")

        # Load the full ag_news dataset (it only has a 'train' split by default)
        logger.info("Loading full 'ag_news' dataset from Hugging Face...")
        full_dataset = load_dataset("ag_news", split="train")
        logger.info(f"Successfully loaded 'ag_news' train split. Total samples: {len(full_dataset)}")

        # Shuffle the dataset for random selection
        logger.info("Shuffling dataset...")
        shuffled_dataset = full_dataset.shuffle(seed=42) # Use a fixed seed for reproducibility
        logger.info("Dataset shuffled.")

        # Select samples for the tiny training set
        if len(shuffled_dataset) < num_train_samples:
            logger.warning(f"Full dataset ({len(shuffled_dataset)}) is smaller than requested num_train_samples ({num_train_samples}). Using all available for train.")
            tiny_train_dataset = shuffled_dataset
        else:
            tiny_train_dataset = shuffled_dataset.select(range(num_train_samples))
        
        logger.info(f"Selected {len(tiny_train_dataset)} samples for the training set.")

        # Select samples for the tiny test set (ensuring they are different from train)
        if len(shuffled_dataset) < num_train_samples + num_test_samples:
            logger.warning(f"Full dataset ({len(shuffled_dataset)}) is too small to select {num_test_samples} distinct test samples after taking {num_train_samples} for train. Adjusting test sample size.")
            # Select remaining samples if any, otherwise it might be empty or very small
            if len(shuffled_dataset) > num_train_samples:
                tiny_test_dataset = shuffled_dataset.select(range(num_train_samples, len(shuffled_dataset)))
            else:
                logger.error("Not enough data for a distinct test set after selecting train samples.")
                tiny_test_dataset = None # Explicitly set to None or handle error
        else:
            tiny_test_dataset = shuffled_dataset.select(range(num_train_samples, num_train_samples + num_test_samples))
        
        if tiny_test_dataset:
            logger.info(f"Selected {len(tiny_test_dataset)} samples for the test set.")
        else:
            logger.error("Failed to create a test dataset.")


        # Define file paths for saving
        train_file_path = os.path.join(output_base_dir, "train.csv")
        test_file_path = os.path.join(output_base_dir, "test.csv")

        # Save the tiny datasets to CSV files
        # The 'text' and 'label' columns are standard for ag_news
        logger.info(f"Saving training set to {train_file_path}...")
        tiny_train_dataset.to_csv(train_file_path, index=False)
        logger.info("Training set saved.")

        if tiny_test_dataset:
            logger.info(f"Saving test set to {test_file_path}...")
            tiny_test_dataset.to_csv(test_file_path, index=False)
            logger.info("Test set saved.")
        else:
            logger.warning(f"Test dataset was not created, so {test_file_path} will not be saved.")


        logger.info(f"Tiny dataset creation complete. Files are in {output_base_dir}")
        logger.info("Make sure 'dataset_path' in your test config points to this directory.")
        logger.info(f"Example test config entry: \"dataset_path\": \"{os.path.abspath(output_base_dir)}\"")


    except Exception as e:
        logger.error(f"An error occurred during tiny dataset creation: {e}", exc_info=True)

if __name__ == "__main__":
    create_tiny_dataset() 