"""
SERP (Search Engine Results Page) Position Tracker
Track keyword rankings over time with DDG and Google CSE
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import os
import json
import csv
from pathlib import Path
from search import ddg_sites
from google_search import google_sites
from logger import get_logger

logger = get_logger(__name__)

SERP_DATA_DIR = Path(__file__).parent / "serp_data"
SERP_DATA_DIR.mkdir(exist_ok=True)


@dataclass
class SERPResult:
    """Single SERP result entry"""
    keyword: str
    position: int
    title: str
    url: str
    snippet: str
    engine: str  # "ddg" or "google"
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "position": self.position,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "engine": self.engine,
            "timestamp": self.timestamp
        }


@dataclass
class SERPSnapshot:
    """Snapshot of SERP for a keyword"""
    keyword: str
    engine: str
    timestamp: str
    results: List[SERPResult]
    total_results: int

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "engine": self.engine,
            "timestamp": self.timestamp,
            "total_results": self.total_results,
            "results": [r.to_dict() for r in self.results]
        }


class SERPTracker:
    """Track keyword positions in search results"""

    def __init__(self, google_api_key: str = "", google_cx: str = ""):
        """
        Initialize SERP tracker

        Args:
            google_api_key: Google Custom Search API key (optional)
            google_cx: Google Custom Search engine ID (optional)
        """
        self.google_api_key = google_api_key
        self.google_cx = google_cx

    def track_keyword(
        self,
        keyword: str,
        engine: str = "ddg",
        max_results: int = 20
    ) -> SERPSnapshot:
        """
        Track current SERP positions for a keyword

        Args:
            keyword: Search keyword to track
            engine: Search engine ("ddg" or "google")
            max_results: Number of results to fetch (default 20)

        Returns:
            SERPSnapshot with current positions
        """
        timestamp = datetime.utcnow().isoformat()
        results = []

        try:
            if engine == "google" and self.google_api_key and self.google_cx:
                urls = self._fetch_google_serp(keyword, max_results)
            else:
                urls = self._fetch_ddg_serp(keyword, max_results)

            # Create SERP results
            for position, url_data in enumerate(urls, start=1):
                result = SERPResult(
                    keyword=keyword,
                    position=position,
                    title=url_data.get("title", ""),
                    url=url_data.get("url", ""),
                    snippet=url_data.get("snippet", ""),
                    engine=engine,
                    timestamp=timestamp
                )
                results.append(result)

            snapshot = SERPSnapshot(
                keyword=keyword,
                engine=engine,
                timestamp=timestamp,
                results=results,
                total_results=len(results)
            )

            # Save snapshot
            self._save_snapshot(snapshot)

            logger.info(f"Tracked SERP for '{keyword}' on {engine}: {len(results)} results")
            return snapshot

        except Exception as e:
            logger.error(f"Error tracking SERP for '{keyword}': {e}")
            return SERPSnapshot(
                keyword=keyword,
                engine=engine,
                timestamp=timestamp,
                results=[],
                total_results=0
            )

    def _fetch_ddg_serp(self, keyword: str, max_results: int) -> List[dict]:
        """Fetch SERP from DuckDuckGo"""
        from duckduckgo_search import DDGS

        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(keyword, max_results=max_results, safesearch="moderate"):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href") or r.get("url", ""),
                        "snippet": r.get("body", "")
                    })
        except Exception as e:
            logger.error(f"DDG SERP fetch error: {e}")

        return results

    def _fetch_google_serp(self, keyword: str, max_results: int) -> List[dict]:
        """Fetch SERP from Google Custom Search"""
        import httpx

        results = []
        if not self.google_api_key or not self.google_cx:
            return results

        try:
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": keyword,
                "num": min(10, max_results),
                "start": 1
            }

            r = httpx.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
            r.raise_for_status()

            data = r.json()
            items = data.get("items", [])

            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })

        except Exception as e:
            logger.error(f"Google SERP fetch error: {e}")

        return results

    def _save_snapshot(self, snapshot: SERPSnapshot):
        """Save SERP snapshot to file"""
        try:
            # Filename: keyword_engine_timestamp.json
            safe_keyword = "".join(c if c.isalnum() else "_" for c in snapshot.keyword)
            filename = f"{safe_keyword}_{snapshot.engine}_{snapshot.timestamp.replace(':', '-')}.json"
            filepath = SERP_DATA_DIR / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved SERP snapshot: {filepath}")

        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")

    def get_history(self, keyword: str, engine: Optional[str] = None) -> List[SERPSnapshot]:
        """
        Get historical snapshots for a keyword

        Args:
            keyword: Keyword to get history for
            engine: Optional engine filter

        Returns:
            List of historical snapshots
        """
        snapshots = []
        safe_keyword = "".join(c if c.isalnum() else "_" for c in keyword)

        try:
            # Find all matching snapshot files
            pattern = f"{safe_keyword}_*.json" if not engine else f"{safe_keyword}_{engine}_*.json"

            for filepath in sorted(SERP_DATA_DIR.glob(pattern)):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Reconstruct snapshot
                    results = [SERPResult(**r) for r in data.get("results", [])]
                    snapshot = SERPSnapshot(
                        keyword=data["keyword"],
                        engine=data["engine"],
                        timestamp=data["timestamp"],
                        total_results=data["total_results"],
                        results=results
                    )
                    snapshots.append(snapshot)

                except Exception as e:
                    logger.error(f"Error loading snapshot {filepath}: {e}")

        except Exception as e:
            logger.error(f"Error getting history for '{keyword}': {e}")

        return snapshots

    def compare_snapshots(
        self,
        snapshot1: SERPSnapshot,
        snapshot2: SERPSnapshot
    ) -> dict:
        """
        Compare two SERP snapshots to detect position changes

        Args:
            snapshot1: Earlier snapshot
            snapshot2: Later snapshot

        Returns:
            Dictionary with comparison results
        """
        if snapshot1.keyword != snapshot2.keyword:
            raise ValueError("Snapshots must be for the same keyword")

        # Build URL position maps
        pos1 = {r.url: r.position for r in snapshot1.results}
        pos2 = {r.url: r.position for r in snapshot2.results}

        # Find changes
        new_entries = []
        dropped_entries = []
        position_changes = []

        # Check for new and changed positions
        for url, pos in pos2.items():
            if url not in pos1:
                new_entries.append({"url": url, "position": pos})
            elif pos1[url] != pos:
                position_changes.append({
                    "url": url,
                    "old_position": pos1[url],
                    "new_position": pos,
                    "change": pos1[url] - pos  # Positive = moved up
                })

        # Check for dropped URLs
        for url, pos in pos1.items():
            if url not in pos2:
                dropped_entries.append({"url": url, "old_position": pos})

        return {
            "keyword": snapshot1.keyword,
            "snapshot1_timestamp": snapshot1.timestamp,
            "snapshot2_timestamp": snapshot2.timestamp,
            "new_entries": new_entries,
            "dropped_entries": dropped_entries,
            "position_changes": position_changes,
            "total_changes": len(new_entries) + len(dropped_entries) + len(position_changes)
        }

    def export_to_csv(self, snapshots: List[SERPSnapshot], output_path: str) -> str:
        """
        Export snapshots to CSV

        Args:
            snapshots: List of snapshots to export
            output_path: Output CSV file path

        Returns:
            Path to exported file
        """
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["keyword", "engine", "timestamp", "position", "title", "url", "snippet"]
                )
                writer.writeheader()

                for snapshot in snapshots:
                    for result in snapshot.results:
                        writer.writerow({
                            "keyword": result.keyword,
                            "engine": result.engine,
                            "timestamp": result.timestamp,
                            "position": result.position,
                            "title": result.title,
                            "url": result.url,
                            "snippet": result.snippet
                        })

            logger.info(f"Exported {len(snapshots)} snapshots to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise

    def track_domain_positions(
        self,
        keyword: str,
        target_domain: str,
        engine: str = "ddg"
    ) -> Optional[int]:
        """
        Track position of a specific domain for a keyword

        Args:
            keyword: Search keyword
            target_domain: Domain to track (e.g., "example.com")
            engine: Search engine to use

        Returns:
            Position (1-indexed) or None if not found
        """
        snapshot = self.track_keyword(keyword, engine)

        for result in snapshot.results:
            if target_domain in result.url:
                logger.info(f"Domain '{target_domain}' found at position {result.position} for '{keyword}'")
                return result.position

        logger.info(f"Domain '{target_domain}' not found in top {len(snapshot.results)} for '{keyword}'")
        return None
