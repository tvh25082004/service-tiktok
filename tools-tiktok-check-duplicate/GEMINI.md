# GEMINI.md

## Project Overview

This project is a Python-based data processing pipeline for analyzing TikTok video data. It focuses on identifying duplicate videos by generating and comparing video hashes.

The core functionalities include:
- **Data Processing:** Parsing raw TikTok data from JSON files into a structured format.
- **Hash Generation:** Creating video hashes using both perceptual hashing (pHash) via the `videohash` library and a custom metadata-based hash.
- **Database Enrichment:** Augmenting the video database with pHash values and 16-bit hash prefixes for efficient pre-filtering.
- **Duplicate Detection:** Identifying duplicate videos by calculating the Hamming distance between their hashes.

The main technologies used are:
- **Python:** The primary programming language.
- **Libraries:**
    - `videohash`: For generating perceptual video hashes.
    - `requests`: For making HTTP requests.
    - `Pillow`: For image processing (a dependency of `videohash`).
    - `yt-dlp`: For downloading video data.

## Building and Running

### 1. Installation

To set up the project, install the required Python dependencies:

```bash
pip3 install -r requirements.txt
```

It is also recommended to have `ffmpeg` installed:

```bash
brew install ffmpeg
```

### 2. Running the Full Pipeline

The `run_processor.sh` script automates the entire data processing workflow. It processes all JSON files located in the `JP_result/` and `result/` directories.

```bash
bash run_processor.sh
```

This script will:
1. Install the necessary dependencies.
2. Execute `process_multiple_datasets.py` to process the datasets and generate the final `data_final.json` file.

### 3. Running Individual Scripts

You can also run the individual Python scripts for more granular control:

- **Process a single TikTok dataset:**
  ```bash
  python3 process_tiktok_dataset.py
  ```
  *(Note: You may need to update the file paths within the script.)*

- **Enrich the database with pHashes:**
  ```bash
  python3 enrich_phash_database.py
  ```

- **Check for duplicate videos:**
  - **Interactive mode:**
    ```bash
    python3 video_duplicate_checker.py
    ```
  - **Command-line mode:**
    ```bash
    python3 video_duplicate_checker.py --url "https://www.tiktok.com/@user/video/1234567890123456789"
    ```

## Development Conventions

- **Coding Style:** The code follows standard Python conventions (PEP 8).
- **Hashing:** The project uses a two-pronged approach to video hashing:
    1.  **pHash:** The primary method for generating a hash based on the video's visual content.
    2.  **Metadata Hash:** A fallback hash generated from the video's metadata (e.g., aweme_id, author, create_time).
- **Duplicate Detection:**
    - A 16-bit prefix of the hash is used for pre-filtering to speed up the comparison process.
    - The Hamming distance is used to measure the similarity between two hashes. A lower distance indicates a higher similarity.
    - The default threshold for considering a video a duplicate is a Hamming distance of 12 or less.
