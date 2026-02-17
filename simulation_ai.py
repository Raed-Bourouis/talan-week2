import csv
import os
import math
from typing import Dict, Any, Tuple

import numpy as np

from sklearn.ensemble import RandomForestRegressor


class SimulationAI:
    """Moteur de simulation SSE utilisant RandomForest + Monte-Carlo.

    Méthodes principales:
    - __init__(price_file): charge les prix depuis un CSV.
    - _train_model(symbol, lag): entraîne un RandomForestRegressor.
    - simulate(symbol, days, n_simulations, lag): génère trajectoires.
    """

    def __init__(self, price_file: str):
        self.price_file = price_file
        self._model_cache: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self.prices: Dict[str, np.ndarray] = {}
        self._load_prices()

    def _load_prices(self) -> None:
        if not os.path.exists(self.price_file):
            raise FileNotFoundError(f"Price file not found: {self.price_file}")

        with open(self.price_file, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            fieldnames = [f.lower() for f in reader.fieldnames or []]

            # detect columns
            date_col = None
            symbol_col = None
            price_col = None

            for f in reader.fieldnames or []:
                fl = f.lower()
                if fl in ('date', 'trade_date') and date_col is None:
                    date_col = f
                if fl in ('symbol', 'ticker') and symbol_col is None:
                    symbol_col = f
                if fl in ('adj_close', 'adjusted_close', 'close', 'close_price', 'price') and price_col is None:
                    price_col = f

            # fallback heuristics
            if symbol_col is None:
                for f in reader.fieldnames or []:
                    if 'sym' in f.lower() or 'ticker' in f.lower():
                        symbol_col = f
                        break
            if price_col is None:
                # try last column
                price_col = (reader.fieldnames or [])[-1]

            for row in reader:
                try:
                    symbol = row[symbol_col].strip() if symbol_col and row.get(symbol_col) is not None else None
                    price_raw = row.get(price_col)
                    if symbol is None or price_raw in (None, ''):
                        continue
                    price = float(price_raw)
                except Exception:
                    continue

                self.prices.setdefault(symbol, []).append((row.get(date_col) if date_col else None, price))

        # convert lists to numpy arrays sorted by date if available
        for symbol, items in list(self.prices.items()):
            # items: list of (date, price)
            if items and items[0][0] is not None:
                try:
                    items_sorted = sorted(items, key=lambda x: x[0])
                except Exception:
                    items_sorted = items
            else:
                items_sorted = items
            prices_arr = np.array([p for (_d, p) in items_sorted], dtype=float)
            if prices_arr.size == 0:
                del self.prices[symbol]
            else:
                self.prices[symbol] = prices_arr

    def _train_model(self, symbol: str, lag: int = 5) -> Dict[str, Any]:
        key = (symbol, lag)
        if key in self._model_cache:
            return self._model_cache[key]

        if symbol not in self.prices:
            raise ValueError(f"Symbol not found in price file: {symbol}")

        prices = self.prices[symbol]
        if prices.size < lag + 2:
            raise ValueError(f"Not enough price data for symbol {symbol} with lag={lag}")

        # use log returns as target and features
        logp = np.log(prices)
        returns = np.diff(logp)  # r_t = log(p_t / p_{t-1})

        n_samples = returns.size - lag
        if n_samples <= 0:
            raise ValueError("Insufficient returns for building training samples")

        X = np.zeros((n_samples, lag), dtype=float)
        y = np.zeros(n_samples, dtype=float)
        for i in range(n_samples):
            X[i, :] = returns[i:i + lag]
            y[i] = returns[i + lag]

        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X, y)

        preds = model.predict(X)
        residuals = y - preds
        resid_std = float(np.std(residuals, ddof=1)) if residuals.size > 1 else float(np.std(residuals))
        resid_std = max(resid_std, 1e-8)

        cache_entry = {
            'model': model,
            'lag': lag,
            'resid_std': resid_std,
            'last_returns': returns[-lag:].copy(),
        }

        self._model_cache[key] = cache_entry
        return cache_entry

    def simulate(self, symbol: str, days: int = 30, n_simulations: int = 1000, lag: int = 5) -> Dict[str, Any]:
        """Simule `n_simulations` trajectoires pour `days` jours.

        Retourne un dict: {mean_path, lower_bound, upper_bound, last_price}
        - mean_path: list de taille days+1 (incluant le last_price au début)
        - lower_bound / upper_bound: percentiles 5% / 95% lists
        - last_price: prix de départ
        """
        if days <= 0 or n_simulations <= 0:
            raise ValueError("days and n_simulations must be positive integers")

        cache = self._train_model(symbol, lag)
        model = cache['model']
        resid_std = cache['resid_std']
        last_returns = cache['last_returns'].copy()

        prices = self.prices[symbol]
        last_price = float(prices[-1])

        rng = np.random.default_rng()
        paths = np.zeros((n_simulations, days + 1), dtype=float)
        paths[:, 0] = last_price

        for sim in range(n_simulations):
            curr_price = last_price
            curr_returns = last_returns.copy()
            for d in range(1, days + 1):
                # predict next return
                try:
                    pred = float(model.predict(curr_returns.reshape(1, -1))[0])
                except Exception as e:
                    raise RuntimeError(f"Model prediction failed: {e}")

                noise = rng.normal(0.0, resid_std)
                r = pred + noise
                curr_price = curr_price * math.exp(r)
                paths[sim, d] = curr_price
                # slide returns window
                curr_returns = np.roll(curr_returns, -1)
                curr_returns[-1] = r

        mean_path = list(np.mean(paths, axis=0))
        lower_bound = list(np.percentile(paths, 5, axis=0))
        upper_bound = list(np.percentile(paths, 95, axis=0))

        return {
            'mean_path': mean_path,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'last_price': last_price,
        }
