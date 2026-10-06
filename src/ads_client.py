from __future__ import annotations

import asyncio
import base64
import gzip
import json
import logging
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

import httpx

RPC_BASE = "https://adstransparency.google.com/anji/_/rpc"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

FORMAT_MAP = {
    "IMAGE": 1,
    "TEXT": 2,
    "VIDEO": 3,
}

FORMAT_REV = {
    1: "IMAGE",
    2: "TEXT",
    3: "VIDEO",
}


def decode_overlay_data(preview_url: str | None) -> dict[str, Any]:
    """Extract headline, display URL and landing link from overlay query param if present."""
    if not preview_url:
        return {}
    m = re.search(r"overlay=([^&]+)", preview_url)
    if not m:
        return {}
    try:
        raw = urllib.parse.unquote(m.group(1))
        if raw.startswith("="):
            raw = raw[1:]
        decomp = gzip.decompress(base64.urlsafe_b64decode(raw + "==")).decode("utf-8", errors="replace")
        headline = None
        destination = None
        m_head = re.search(r"headline\s*\d*\s*[\.\:\-\s]*([^\n\r\t\x00-\x1f]{4,120})", decomp)
        if m_head:
            headline = m_head.group(1).strip()
        m_vis = re.search(r"(https?://[^\s\x00-\x1f\"\'<>]{8,300})", decomp)
        if m_vis:
            destination = m_vis.group(1).strip()
        out = {}
        if headline:
            out["headline"] = headline
        if destination:
            out["destinationUrl"] = destination
        return out
    except Exception:
        return {}


class GoogleAdsClient:
    def __init__(
        self,
        proxy_factory: Callable[[str], Awaitable[str | None]] | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        self.proxy_factory = proxy_factory
        self.log = log or logging.getLogger(__name__)
        self.stats = {"requests": 0, "retries": 0, "errors": 0}

    async def _post_rpc(self, service_method: str, payload_dict: dict, session_id: str = "sess1") -> dict:
        url = f"{RPC_BASE}/{service_method}?authuser="
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
            "Referer": "https://adstransparency.google.com/",
            "Origin": "https://adstransparency.google.com",
            "Accept": "*/*",
        }
        data = {"f.req": json.dumps(payload_dict)}

        for attempt in range(4):
            proxy_url = await self.proxy_factory(f"{session_id}_{attempt}") if self.proxy_factory else None
            self.stats["requests"] += 1
            try:
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    timeout=httpx.Timeout(20.0, connect=10.0),
                    follow_redirects=True,
                ) as client:
                    resp = await client.post(url, data=data, headers=headers)
                    if resp.status_code == 200:
                        return resp.json()
                    if resp.status_code in (429, 503):
                        self.log.warning(f"RPC {service_method} rate-limited ({resp.status_code}), attempt {attempt + 1}")
                        self.stats["retries"] += 1
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    self.log.warning(f"RPC {service_method} returned HTTP {resp.status_code}")
            except Exception as err:
                self.stats["retries"] += 1
                self.log.warning(f"RPC request failed (attempt {attempt + 1}): {err}")
                await asyncio.sleep(1.0 * (attempt + 1))

        self.stats["errors"] += 1
        raise RuntimeError(f"RPC {service_method} failed after 4 retries.")

    async def search_suggestions(self, query: str) -> list[dict[str, Any]]:
        """Resolve a brand or domain query into matching advertisers."""
        payload = {"1": query.strip(), "2": 10, "3": 10, "5": {"1": 1}}
        data = await self._post_rpc("SearchService/SearchSuggestions", payload, session_id="sugg")
        results = []
        raw_items = data.get("1", [])
        for item in raw_items:
            adv = item.get("1")
            dom = item.get("2")
            if adv:
                results.append({
                    "type": "ADVERTISER",
                    "advertiserName": adv.get("1"),
                    "advertiserId": adv.get("2"),
                    "country": adv.get("3"),
                })
            elif dom:
                results.append({
                    "type": "DOMAIN",
                    "domain": dom.get("1"),
                })
        return results

    async def fetch_creatives_page(
        self,
        query: str,
        page_size: int = 40,
        format_code: int | None = None,
        cursor: str | None = None,
        session_id: str = "creatives",
    ) -> tuple[list[dict[str, Any]], str | None, dict[str, int]]:
        """Fetch one page of ad creatives from Google Ads Transparency."""
        is_adv_id = query.startswith("AR") and len(query) > 10
        sub3: dict[str, Any] = {"13": {"1": [query]}} if is_adv_id else {"12": {"1": query}}
        if format_code in (1, 2, 3):
            sub3["4"] = format_code

        payload: dict[str, Any] = {"2": max(5, min(page_size, 40)), "3": sub3, "7": {"1": 1}}
        if cursor:
            payload["4"] = cursor

        data = await self._post_rpc("SearchService/SearchCreatives", payload, session_id=session_id)
        raw_creatives = data.get("1", [])
        next_cursor = data.get("2")
        counts = {
            "lowerBound": int(data.get("4") or 0),
            "upperBound": int(data.get("5") or 0),
        }

        records = []
        for item in raw_creatives:
            adv_id = item.get("1")
            creative_id = item.get("2")
            fmt = item.get("4")
            fmt_str = FORMAT_REV.get(fmt, "OTHER")

            first_ts = int(item.get("6", {}).get("1", 0) or 0)
            last_ts = int(item.get("7", {}).get("1", 0) or 0)
            first_iso = datetime.fromtimestamp(first_ts, tz=timezone.utc).isoformat() if first_ts else None
            last_iso = datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat() if last_ts else None
            days_active = round((last_ts - first_ts) / 86400, 1) if (first_ts and last_ts and last_ts >= first_ts) else 0

            # Image & Preview links
            image_url = None
            if fmt == 1:
                img_tag = item.get("3", {}).get("3", {}).get("2", "")
                m_img = re.search(r'src=["\']([^"\']+)["\']', img_tag)
                if m_img:
                    image_url = m_img.group(1)

            preview_script = item.get("3", {}).get("1", {}).get("4", "")
            overlay_info = decode_overlay_data(preview_script)

            canonical_url = f"https://adstransparency.google.com/advertiser/{adv_id}/creative/{creative_id}?region=anywhere"

            record = {
                "creativeId": creative_id,
                "advertiserId": adv_id,
                "advertiserName": item.get("12"),
                "targetDomain": item.get("14") or (query if not is_adv_id else None),
                "format": fmt_str,
                "firstShown": first_iso,
                "lastShown": last_iso,
                "daysActive": days_active,
                "imageUrl": image_url,
                "transparencyUrl": canonical_url,
                **overlay_info,
            }
            records.append(record)

        return records, next_cursor, counts
