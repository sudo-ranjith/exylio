"""
Exylio Radar Module
Macro Event Intelligence Engine
Monitors GDELT + NewsAPI + RSS for market-moving events.
"""
import httpx, feedparser, json
from datetime import datetime
from logzero import logger
from app.core.config import settings

# ── Sector Impact Matrix ──────────────────────────────────────────
SECTOR_IMPACT_MATRIX = {
    "WAR": {
        "rise": [
            {"sector": "Defence",       "stocks": ["HAL", "BEL", "BHEL"],         "confidence": 0.90},
            {"sector": "Energy",        "stocks": ["ONGC", "OIL"],                "confidence": 0.85},
            {"sector": "Metals",        "stocks": ["HINDALCO", "TATASTEEL"],       "confidence": 0.70},
            {"sector": "Pharma",        "stocks": ["SUNPHARMA", "DRREDDY"],        "confidence": 0.65},
            {"sector": "IT",            "stocks": ["TCS", "INFY", "WIPRO"],        "confidence": 0.60},
        ],
        "fall": [
            {"sector": "Aviation",      "stocks": ["INDIGO"],                      "confidence": 0.90},
            {"sector": "Auto",          "stocks": ["MARUTI", "TATAMOTORS", "MM"],  "confidence": 0.85},
            {"sector": "Paints",        "stocks": ["ASIANPAINT"],                  "confidence": 0.80},
            {"sector": "Banking",       "stocks": ["HDFCBANK", "ICICIBANK"],       "confidence": 0.70},
            {"sector": "RealEstate",    "stocks": ["DLF", "GODREJPROP"],           "confidence": 0.65},
        ],
    },
    "CRUDE": {
        "rise": [
            {"sector": "Energy",        "stocks": ["ONGC", "OIL", "RELIANCE"],    "confidence": 0.90},
            {"sector": "Coal",          "stocks": ["COALINDIA"],                   "confidence": 0.65},
        ],
        "fall": [
            {"sector": "Aviation",      "stocks": ["INDIGO"],                      "confidence": 0.95},
            {"sector": "Paints",        "stocks": ["ASIANPAINT", "PIDILITIND"],   "confidence": 0.85},
            {"sector": "Auto",          "stocks": ["MARUTI", "TATAMOTORS"],        "confidence": 0.80},
        ],
    },
    "RBI_RATE_CUT": {
        "rise": [
            {"sector": "Banking",       "stocks": ["HDFCBANK", "ICICIBANK", "AXISBANK"], "confidence": 0.85},
            {"sector": "RealEstate",    "stocks": ["DLF", "GODREJPROP"],           "confidence": 0.90},
            {"sector": "NBFC",          "stocks": ["BAJFINANCE", "SBICARD"],       "confidence": 0.80},
        ],
        "fall": [],
    },
    "RBI_RATE_HIKE": {
        "rise": [],
        "fall": [
            {"sector": "Banking",       "stocks": ["HDFCBANK", "ICICIBANK"],       "confidence": 0.80},
            {"sector": "RealEstate",    "stocks": ["DLF", "OBEROIRLTY"],           "confidence": 0.85},
        ],
    },
    "FED": {
        "rise": [],
        "fall": [
            {"sector": "IT",            "stocks": ["TCS", "INFY", "WIPRO", "HCLTECH"], "confidence": 0.75},
            {"sector": "Banking",       "stocks": ["HDFCBANK", "ICICIBANK"],       "confidence": 0.70},
        ],
    },
    "ELECTION": {
        "rise": [
            {"sector": "PSU Banks",     "stocks": ["SBIN"],                        "confidence": 0.70},
            {"sector": "Infrastructure","stocks": ["LT", "NTPC"],                  "confidence": 0.75},
            {"sector": "Defence",       "stocks": ["HAL", "BEL"],                  "confidence": 0.70},
        ],
        "fall": [],
    },
    "RECESSION": {
        "rise": [
            {"sector": "FMCG",          "stocks": ["HINDUNILVR", "BRITANNIA"],     "confidence": 0.75},
            {"sector": "Pharma",        "stocks": ["SUNPHARMA", "DRREDDY"],        "confidence": 0.70},
        ],
        "fall": [
            {"sector": "IT",            "stocks": ["TCS", "INFY", "WIPRO"],        "confidence": 0.80},
            {"sector": "Metals",        "stocks": ["HINDALCO", "TATASTEEL"],       "confidence": 0.85},
        ],
    },
}

# ── Event keyword filters ─────────────────────────────────────────
EVENT_KEYWORDS = {
    "WAR":          ["war", "airstrike", "military", "invasion", "troops", "ceasefire", "missile"],
    "GEOPOLITICAL": ["sanctions", "embargo", "expelled", "tariff", "tensions", "dispute"],
    "CRUDE":        ["OPEC", "crude", "oil price", "Brent", "WTI", "supply cut", "refinery"],
    "RBI":          ["RBI", "repo rate", "CRR", "monetary policy", "MPC", "inflation"],
    "FED":          ["Federal Reserve", "Fed", "FOMC", "rate hike", "rate cut", "taper"],
    "ELECTION":     ["election", "BJP", "Congress", "exit poll", "vote count", "election result"],
    "BUDGET":       ["budget", "fiscal deficit", "capex", "divestment", "tax slab", "Finance Minister"],
    "RECESSION":    ["recession", "GDP miss", "PMI", "bank failure", "credit crunch"],
    "DISASTER":     ["earthquake", "flood", "cyclone", "tsunami", "outbreak", "pandemic"],
}

# ── RSS Feeds ─────────────────────────────────────────────────────
RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.rbi.org.in/Scripts/rss.aspx",
]


class RadarEngine:

    def classify_event(self, text: str) -> tuple[str, float]:
        """Returns (event_type, confidence)."""
        text_lower = text.lower()
        scores = {}
        for event_type, keywords in EVENT_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw.lower() in text_lower)
            if hits:
                scores[event_type] = hits / len(keywords)

        if not scores:
            return "UNKNOWN", 0.0

        best_type = max(scores, key=scores.get)
        return best_type, min(scores[best_type] * 2, 1.0)  # normalize

    def calculate_severity(
        self, goldstein: float = 0,
        article_count: int = 1,
        avg_tone: float = 0,
        fii_net: float = 0,
    ) -> tuple[int, str]:
        """Returns (score 0-100, label)."""
        # Goldstein: -10 worst → 0 neutral → +10 best
        goldstein_norm = max(0, (-goldstein + 10) / 20 * 100)
        g_component    = goldstein_norm * 0.35

        # Article volume (log scale)
        import math
        vol_norm    = min(math.log(max(article_count, 1) + 1) / math.log(101), 1) * 100
        v_component = vol_norm * 0.25

        # Avg tone: negative = bad
        tone_norm   = max(0, (-avg_tone) / 100 * 100)
        t_component = tone_norm * 0.20

        # FII net sell
        fii_component = 20 if fii_net < -1000 else 0
        fii_component *= 0.20

        score = int(g_component + v_component + t_component + fii_component)
        score = max(0, min(score, 100))

        if score >= 81:  label = "EXTREME"
        elif score >= 56: label = "HIGH"
        elif score >= 31: label = "MEDIUM"
        else:             label = "LOW"

        return score, label

    async def fetch_gdelt_events(self) -> list[dict]:
        """Fetch latest GDELT events relevant to Indian markets."""
        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc"
            "?query=India+market+economy&mode=artlist&maxrecords=25"
            "&format=json&timespan=15m"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json().get("articles", [])
        except Exception as e:
            logger.error(f"GDELT fetch error: {e}")
        return []

    async def fetch_rss_news(self) -> list[dict]:
        """Fetch Indian financial news from RSS feeds."""
        articles = []
        for feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    articles.append({
                        "title":   entry.get("title", ""),
                        "summary": entry.get("summary", ""),
                        "source":  feed_url,
                        "time":    datetime.now().isoformat(),
                    })
            except Exception as e:
                logger.error(f"RSS error {feed_url}: {e}")
        return articles

    async def fetch_newsapi(self, query: str = "India stock market") -> list[dict]:
        """Fetch from NewsAPI.org."""
        if not settings.NEWS_API_KEY:
            return []
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={query}&language=en&sortBy=publishedAt"
            f"&pageSize=20&apiKey={settings.NEWS_API_KEY}"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json().get("articles", [])
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
        return []

    async def run_radar_cycle(self) -> list[dict]:
        """
        Full radar cycle: fetch → classify → score → map sectors.
        Returns list of RadarEvent dicts ready for DB + alerting.
        """
        events = []

        # Fetch from all sources
        rss_articles   = await self.fetch_rss_news()
        news_articles  = await self.fetch_newsapi()
        all_articles   = rss_articles + news_articles

        seen_types = set()
        for article in all_articles:
            text = f"{article.get('title', '')} {article.get('summary', article.get('description', ''))}"
            event_type, confidence = self.classify_event(text)

            if event_type == "UNKNOWN" or confidence < 0.3:
                continue
            if event_type in seen_types:     # deduplicate per cycle
                continue
            seen_types.add(event_type)

            score, label = self.calculate_severity(
                goldstein=-2, article_count=len(all_articles), avg_tone=-15
            )

            impact = SECTOR_IMPACT_MATRIX.get(event_type, {"rise": [], "fall": []})
            event  = {
                "event_id":      f"RADAR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{event_type}",
                "event_type":    event_type,
                "severity_score": score,
                "severity_label": label,
                "confidence":    round(confidence, 2),
                "headline":      article.get("title", "")[:120],
                "source_count":  len(all_articles),
                "sources":       [article.get("source", "")],
                "sectors_rise":  impact["rise"],
                "sectors_fall":  impact["fall"],
                "detected_at":   datetime.now().isoformat(),
            }
            events.append(event)
            logger.info(f"🔭 Radar: {event_type} [{label}] — {event['headline'][:60]}")

        return events

    def cross_check_portfolio(self, radar_event: dict, holdings: list[dict]) -> list[dict]:
        """
        For each holding, check if its sector is in rise/fall list.
        Returns position alerts with risk scores and recommendations.
        """
        alerts = []
        fall_sectors = {s["sector"] for s in radar_event.get("sectors_fall", [])}
        rise_sectors = {s["sector"] for s in radar_event.get("sectors_rise", [])}
        severity     = radar_event.get("severity_score", 0)

        for holding in holdings:
            sector = holding.get("sector", "")
            days   = holding.get("holding_days", 0)
            duration_weight = 1.0 + (days / 5 * 0.3)   # longer held = higher risk weight

            if sector in fall_sectors:
                conf = next(
                    (s["confidence"] for s in radar_event["sectors_fall"] if s["sector"] == sector), 0.5
                )
                risk_score = int(severity * conf * duration_weight)
                risk_score = min(risk_score, 100)

                if risk_score >= 81 or days >= 4:
                    recommendation = "EXIT"
                elif risk_score >= 61:
                    recommendation = "REVIEW"
                elif risk_score >= 31:
                    recommendation = "WATCH"
                else:
                    recommendation = "HOLD"

                alerts.append({
                    "ticker":          holding["ticker"],
                    "sector":          sector,
                    "event_risk_score": risk_score,
                    "recommendation":  recommendation,
                    "reasoning":       f"{sector} is a FALL sector for {radar_event['event_type']} event",
                })

            elif sector in rise_sectors:
                alerts.append({
                    "ticker":         holding["ticker"],
                    "sector":         sector,
                    "event_risk_score": 10,
                    "recommendation": "HOLD",
                    "reasoning":      f"{sector} is a RISE sector — continue holding",
                })

        return alerts


radar_engine = RadarEngine()
