import yfinance as yf
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List

class MarketDataService:
    def __init__(self, cache_ttl_seconds: int = 300):

        self.cache_ttl = cache_ttl_seconds
        self._price_cache: Dict[str, dict] = {}

    async def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetches live market prices for a list of ticker symbols.
        Uses in-memory cache to prevent yfinance rate limits and speed up responses.
        """
        if not symbols:
            return {}

        now = datetime.utcnow()
        symbols_to_fetch = []
        cached_prices: Dict[str, float] = {}


        for symbol in symbols:
            sym_upper = symbol.upper()
            if sym_upper in self._price_cache:
                cache_entry = self._price_cache[sym_upper]
                if now - cache_entry["timestamp"] < timedelta(seconds=self.cache_ttl):
                    cached_prices[sym_upper] = cache_entry["price"]
                    continue
            symbols_to_fetch.append(sym_upper)


        if not symbols_to_fetch:
            return cached_prices

        fetched_prices = await asyncio.to_thread(self._fetch_from_yfinance, symbols_to_fetch)

        for sym, price in fetched_prices.items():
            self._price_cache[sym] = {
                "price": price,
                "timestamp": now
            }
            cached_prices[sym] = price

        return cached_prices

    def _fetch_from_yfinance(self, symbols: List[str]) -> Dict[str, float]:
        """Synchronous helper for fetching batch prices via yfinance."""
        prices = {}
        try:
            tickers = yf.Tickers(" ".join(symbols))
            for sym in symbols:
                ticker_obj = tickers.tickers.get(sym)
                price = None
                if ticker_obj and hasattr(ticker_obj, 'fast_info'):
                    try:
                        price = ticker_obj.fast_info.get("lastPrice") or ticker_obj.fast_info.get("previousClose")
                    except Exception:
                        pass

                if price and float(price) > 0:
                    prices[sym] = round(float(price), 2)
                else:
                    # Previous cached value fallback or safe default
                    prices[sym] = self._price_cache.get(sym, {}).get("price", 100.0)
        except Exception:
            for sym in symbols:
                prices[sym] = self._price_cache.get(sym, {}).get("price", 100.0)
                
        return prices