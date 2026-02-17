import os
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from typing import Tuple, List, Dict, Optional
import warnings

import faiss
from sentence_transformers import SentenceTransformer

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path('nyse_data')
MODEL_DIR = Path('models')
FAISS_INDEX_PATH = MODEL_DIR / 'faiss_index.bin'
SYMBOLS_PKL_PATH = MODEL_DIR / 'symbols.pkl'
CACHE_DIR = Path('.cache')
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'


def ensure_directories_exist():
    """Create necessary directories if they don't exist."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {MODEL_DIR}, {CACHE_DIR}")


def load_and_preprocess_data() -> pd.DataFrame:
    """
    Load and preprocess NYSE data from CSV files.
    
    Returns:
        pd.DataFrame: Preprocessed company-level DataFrame indexed by symbol.
    
    Raises:
        FileNotFoundError: If required CSV files are missing.
    """
    logger.info("Starting data loading and preprocessing...")
    
    # Verify files exist
    required_files = {
        'prices': DATA_DIR / 'prices-split-adjusted.csv',
        'securities': DATA_DIR / 'securities.csv',
        'fundamentals': DATA_DIR / 'fundamentals.csv'
    }
    
    for file_type, file_path in required_files.items():
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required file: {file_path}")
        logger.info(f"Found {file_type} file: {file_path}")
    
    # Load CSV files
    logger.info("Loading CSV files...")
    try:
        prices_df = pd.read_csv(required_files['prices'])
        securities_df = pd.read_csv(required_files['securities'])
        fundamentals_df = pd.read_csv(required_files['fundamentals'])
        logger.info(f"Loaded prices: {prices_df.shape}, securities: {securities_df.shape}, fundamentals: {fundamentals_df.shape}")
    except Exception as e:
        logger.error(f"Error loading CSV files: {e}")
        raise
    
    # Preprocess Securities: Create text_description
    logger.info("Creating text_description for securities...")
    securities_df['text_description'] = securities_df.apply(
        lambda row: f"Company: {row.get('Security', 'N/A')}. "
                   f"Sector: {row.get('GICS Sector', 'N/A')}. "
                   f"Sub-Industry: {row.get('GICS Sub-Industry', 'N/A')}. "
                   f"Address: {row.get('Address of Headquarters', 'N/A')}. "
                   f"Date Added: {row.get('Date first added', 'N/A')}.",
        axis=1
    )
    
    # Preprocess Fundamentals: Compute financial ratios (robust column detection)
    logger.info("Computing financial ratios from fundamentals...")

    def find_column(df, candidates):
        """Return first matching column name from candidates (case-insensitive), or None."""
        cols_lower = {c.lower(): c for c in df.columns}
        for cand in candidates:
            if cand is None:
                continue
            key = cand.lower()
            if key in cols_lower:
                return cols_lower[key]
        return None

    # candidate names for common fields (covers variations in CSVs)
    debt_cols = ['Total Debt', 'Total debt', 'total_debt', 'Long Term Debt', 'Long-Term Debt', 'Long term debt', 'Total Liabilities']
    equity_cols = ['Total Stockholders Equity', "Total Stockholders' Equity", 'Total Stockholders Equity', 'Total Equity', 'Total equity', 'total_equity']
    net_income_cols = ['Net Income', 'Net income', 'NetIncome', 'Net_Income']
    assets_cols = ['Total Assets', 'Total assets', 'TotalAssets', 'Total_Assets']
    current_assets_cols = ['Current Assets', 'Current assets', 'CurrentAssets', 'Current_Assets']
    current_liabilities_cols = ['Current Liabilities', 'Current liabilities', 'CurrentLiabilities', 'Current_Liabilities']

    col_debt = find_column(fundamentals_df, debt_cols)
    col_equity = find_column(fundamentals_df, equity_cols)
    col_net_income = find_column(fundamentals_df, net_income_cols)
    col_assets = find_column(fundamentals_df, assets_cols)
    col_current_assets = find_column(fundamentals_df, current_assets_cols)
    col_current_liabilities = find_column(fundamentals_df, current_liabilities_cols)

    # Convert found columns to numeric; if not found, create zero-filled series
    def to_numeric_series(col_name):
        if col_name and col_name in fundamentals_df.columns:
            return pd.to_numeric(fundamentals_df[col_name], errors='coerce').fillna(0)
        else:
            return pd.Series(0, index=fundamentals_df.index)

    debt_s = to_numeric_series(col_debt)
    equity_s = to_numeric_series(col_equity)
    net_income_s = to_numeric_series(col_net_income)
    assets_s = to_numeric_series(col_assets)
    current_assets_s = to_numeric_series(col_current_assets)
    current_liabilities_s = to_numeric_series(col_current_liabilities)

    # Attach canonical columns to DataFrame for later use
    fundamentals_df['__debt'] = debt_s
    fundamentals_df['__equity'] = equity_s
    fundamentals_df['__net_income'] = net_income_s
    fundamentals_df['__assets'] = assets_s
    fundamentals_df['__current_assets'] = current_assets_s
    fundamentals_df['__current_liabilities'] = current_liabilities_s

    # Calculate ratios with safe division
    fundamentals_df['Debt_to_Equity'] = np.where(
        fundamentals_df['__equity'] != 0,
        fundamentals_df['__debt'] / fundamentals_df['__equity'],
        np.nan
    )
    fundamentals_df['ROE'] = np.where(
        fundamentals_df['__equity'] != 0,
        fundamentals_df['__net_income'] / fundamentals_df['__equity'],
        np.nan
    )
    fundamentals_df['ROA'] = np.where(
        fundamentals_df['__assets'] != 0,
        fundamentals_df['__net_income'] / fundamentals_df['__assets'],
        np.nan
    )
    fundamentals_df['Current_Ratio'] = np.where(
        fundamentals_df['__current_liabilities'] != 0,
        fundamentals_df['__current_assets'] / fundamentals_df['__current_liabilities'],
        np.nan
    )
    
    # Get latest fundamentals per symbol
    logger.info("Extracting latest fundamentals per symbol...")
    if 'Ticker Symbol' in fundamentals_df.columns:
        fundamentals_latest = fundamentals_df.loc[
            fundamentals_df.groupby('Ticker Symbol')['Period Ending'].idxmax()
        ].copy()
        fundamentals_latest = fundamentals_latest.set_index('Ticker Symbol')
    else:
        logger.warning("'Ticker Symbol' column not found in fundamentals. Skipping fundamentals merge.")
        fundamentals_latest = pd.DataFrame()
    
    # Preprocess Prices: Calculate latest closing price and volatility
    logger.info("Calculating price statistics...")
    if 'symbol' in prices_df.columns and 'close' in prices_df.columns:
        prices_df['date'] = pd.to_datetime(prices_df['date'], errors='coerce')
        
        # Latest closing price
        latest_prices = prices_df.loc[prices_df.groupby('symbol')['date'].idxmax()].copy()
        latest_prices_dict = dict(zip(latest_prices['symbol'], latest_prices['close']))
        
        # Daily volatility (standard deviation of daily returns)
        prices_df['daily_return'] = prices_df.groupby('symbol')['close'].pct_change()
        volatility = prices_df.groupby('symbol')['daily_return'].std()
        volatility_dict = volatility.to_dict()
    else:
        logger.warning("Expected price columns not found. Using defaults.")
        latest_prices_dict = {}
        volatility_dict = {}
    
    # Build company-level DataFrame
    logger.info("Building company-level DataFrame...")
    securities_df = securities_df.set_index('Ticker symbol')
    
    company_df = pd.DataFrame()
    company_df['text_description'] = securities_df['text_description']
    company_df['sector'] = securities_df.get('GICS Sector', 'Unknown')
    company_df['latest_close'] = company_df.index.map(latest_prices_dict).fillna(0)
    company_df['volatility'] = company_df.index.map(volatility_dict).fillna(0)
    
    # Merge financial ratios
    if not fundamentals_latest.empty:
        ratio_cols = ['Debt_to_Equity', 'ROE', 'ROA', 'Current_Ratio']
        for col in ratio_cols:
            if col in fundamentals_latest.columns:
                company_df[col] = fundamentals_latest[col]
            else:
                company_df[col] = np.nan
    else:
        company_df['Debt_to_Equity'] = np.nan
        company_df['ROE'] = np.nan
        company_df['ROA'] = np.nan
        company_df['Current_Ratio'] = np.nan
    
    # Fill missing values
    company_df = company_df.fillna(0)
    
    logger.info(f"Company DataFrame created: {company_df.shape}")
    logger.info(f"Columns: {company_df.columns.tolist()}")
    
    return company_df


def build_vector_store(company_df: pd.DataFrame) -> Tuple[faiss.IndexFlatL2, List[str]]:
    """
    Build FAISS vector store from company text descriptions.
    
    Args:
        company_df: DataFrame with text_description column.
    
    Returns:
        Tuple of (FAISS index, list of symbols).
    """
    logger.info("Building vector store...")
    
    # Load pre-trained sentence transformer
    logger.info(f"Loading SentenceTransformer model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Generate embeddings
    logger.info(f"Generating embeddings for {len(company_df)} companies...")
    texts = company_df['text_description'].tolist()
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    # Create FAISS index
    logger.info(f"Creating FAISS IndexFlatL2 with embedding dimension: {embeddings.shape[1]}")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings.astype(np.float32))
    
    # Get symbols list
    symbols = company_df.index.tolist()
    
    logger.info(f"Vector store built with {index.ntotal} vectors")
    
    return index, symbols


def save_vector_store(index: faiss.IndexFlatL2, symbols: List[str]) -> None:
    """
    Save FAISS index and symbols to disk.
    
    Args:
        index: FAISS index.
        symbols: List of symbols.
    """
    logger.info(f"Saving FAISS index to {FAISS_INDEX_PATH}")
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    
    logger.info(f"Saving symbols to {SYMBOLS_PKL_PATH}")
    with open(SYMBOLS_PKL_PATH, 'wb') as f:
        pickle.dump(symbols, f)


def load_vector_store() -> Tuple[Optional[faiss.IndexFlatL2], Optional[List[str]]]:
    """
    Load FAISS index and symbols from disk if they exist.
    
    Returns:
        Tuple of (FAISS index, symbols) or (None, None) if not found.
    """
    if FAISS_INDEX_PATH.exists() and SYMBOLS_PKL_PATH.exists():
        logger.info(f"Loading FAISS index from {FAISS_INDEX_PATH}")
        index = faiss.read_index(str(FAISS_INDEX_PATH))
        
        logger.info(f"Loading symbols from {SYMBOLS_PKL_PATH}")
        with open(SYMBOLS_PKL_PATH, 'rb') as f:
            symbols = pickle.load(f)
        
        logger.info(f"Vector store loaded: {index.ntotal} vectors, {len(symbols)} symbols")
        return index, symbols
    
    logger.info("Vector store not found. Will be built from scratch.")
    return None, None


def semantic_search(query: str, k: int = 5, index: Optional[faiss.IndexFlatL2] = None, 
                   symbols: Optional[List[str]] = None, model: Optional[SentenceTransformer] = None) -> List[Tuple[str, float]]:
    """
    Perform semantic search on the company database.
    
    Args:
        query: Search query string.
        k: Number of top results to return.
        index: FAISS index (loaded if not provided).
        symbols: List of symbols (loaded if not provided).
        model: SentenceTransformer model (loaded if not provided).
    
    Returns:
        List of (symbol, distance) tuples.
    
    Raises:
        RuntimeError: If vector store is not available.
    """
    # Load components if not provided
    if index is None or symbols is None:
        index, symbols = load_vector_store()
        if index is None or symbols is None:
            raise RuntimeError("Vector store not available. Run build_vector_store() first.")
    
    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Encode query
    logger.info(f"Searching for: '{query}'")
    query_embedding = model.encode([query], convert_to_numpy=True).astype(np.float32)
    
    # Search
    distances, indices = index.search(query_embedding, k)
    
    # Format results
    results = [
        (symbols[idx], float(dist)) 
        for idx, dist in zip(indices[0], distances[0])
    ]
    
    logger.info(f"Found {len(results)} results")
    return results


def main():
    """Main entry point for the cognitive ingestion script."""
    logger.info("=" * 60)
    logger.info("Starting NYSE Cognitive Ingestion Pipeline")
    logger.info("=" * 60)
    
    try:
        ensure_directories_exist()
        
        # Load and preprocess data
        company_df = load_and_preprocess_data()
        
        # Check if vector store already exists
        index, symbols = load_vector_store()
        
        if index is None or symbols is None:
            # Build and save vector store
            index, symbols = build_vector_store(company_df)
            save_vector_store(index, symbols)
            logger.info("Vector store saved successfully")
        else:
            logger.info("Using existing vector store (caching)")
        
        # Example semantic search
        logger.info("\n" + "=" * 60)
        logger.info("Example Semantic Search")
        logger.info("=" * 60)
        
        test_queries = [
            "technology companies",
            "financial sector",
            "healthcare industry"
        ]
        
        model = SentenceTransformer(EMBEDDING_MODEL)
        
        for query in test_queries:
            logger.info(f"\nQuery: '{query}'")
            results = semantic_search(query, k=5, index=index, symbols=symbols, model=model)
            for symbol, distance in results:
                logger.info(f"  {symbol}: {distance:.4f}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline completed successfully")
        logger.info("=" * 60)
        
        return company_df, index, symbols
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    company_df, index, symbols = main()
