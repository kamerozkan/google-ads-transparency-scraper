from __future__ import annotations

import asyncio
from typing import Any

from apify import Actor
from ads_client import GoogleAdsClient, FORMAT_MAP


class ChargeLimitReached(Exception):
    pass


class Runner:
    def __init__(self, inp: dict[str, Any], client: GoogleAdsClient) -> None:
        self.client = client
        self.pushed = 0
        self.failed: list[dict[str, Any]] = []
        self.stop = False
        self.sem = asyncio.Semaphore(int(inp.get("maxConcurrency") or 5))

    async def push_creative(self, record: dict[str, Any]) -> None:
        if self.stop:
            return

        # Pay-per-event charge
        try:
            await Actor.charge(event_name="ad-creative")
        except Exception as err:
            err_msg = str(err).lower()
            if "budget" in err_msg or "limit" in err_msg or "charge" in err_msg:
                Actor.log.warning(f"Spending limit reached: {err}. Halting scraping.")
                self.stop = True
                raise ChargeLimitReached() from err
            Actor.log.debug(f"Non-fatal charge notice: {err}")

        await Actor.push_data(record)
        self.pushed += 1

    async def run_query(self, query: str, max_ads: int, format_code: int | None) -> None:
        if self.stop:
            return
        Actor.log.info(f"Scraping ads for '{query}' (limit={max_ads}, format={format_code or 'ALL'})...")
        cursor = None
        count_for_query = 0

        while count_for_query < max_ads and not self.stop:
            async with self.sem:
                try:
                    records, next_cursor, counts = await self.client.fetch_creatives_page(
                        query=query,
                        page_size=min(40, max_ads - count_for_query),
                        format_code=format_code,
                        cursor=cursor,
                        session_id=query,
                    )
                except Exception as err:
                    Actor.log.warning(f"Error fetching ads for '{query}': {err}")
                    self.failed.append({"query": query, "error": str(err)[:300]})
                    break

            if not records:
                if count_for_query == 0:
                    Actor.log.info(f"No active ads found for '{query}'.")
                break

            for rec in records:
                if self.stop:
                    break
                await self.push_creative(rec)
                count_for_query += 1
                if count_for_query >= max_ads:
                    break

            cursor = next_cursor
            if not cursor:
                break

        Actor.log.info(f"Finished '{query}': {count_for_query} ads collected.")


async def main() -> None:
    async with Actor:
        inp: dict[str, Any] = await Actor.get_input() or {}
        queries = [q.strip() for q in inp.get("queries") or [] if isinstance(q, str) and q.strip()]

        if not queries:
            await Actor.fail(
                status_message="Please provide at least one query (e.g. domain 'nike.com' or advertiser ID 'AR...')."
            )
            return

        fmt_str = (inp.get("format") or "ALL").upper()
        fmt_code = FORMAT_MAP.get(fmt_str)
        max_ads = max(1, min(int(inp.get("maxAdsPerQuery") or 40), 1000))

        proxy_cfg = await Actor.create_proxy_configuration(actor_proxy_input=inp.get("proxyConfiguration"))

        async def proxy_factory(session: str) -> str | None:
            return await proxy_cfg.new_url(session_id=session) if proxy_cfg else None

        client = GoogleAdsClient(proxy_factory if proxy_cfg else None, log=Actor.log)
        runner = Runner(inp, client)

        Actor.log.info(
            f"Starting Google Ads Transparency Scraper: {len(queries)} queries, "
            f"format={fmt_str}, maxAdsPerQuery={max_ads}"
        )
        await Actor.set_status_message(f"Scraping ads for {len(queries)} queries...")

        tasks = [runner.run_query(q, max_ads, fmt_code) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception) and not isinstance(r, ChargeLimitReached):
                Actor.log.exception(r)

        summary = {
            "adsCollected": runner.pushed,
            "failedQueries": len(runner.failed),
            "failures": runner.failed[:100],
            "rpcRequests": client.stats,
        }
        await Actor.set_value("RUN_SUMMARY", summary)

        msg = f"Completed: {runner.pushed} ads scraped"
        if runner.failed:
            msg += f", {len(runner.failed)} query errors"
        Actor.log.info(msg)
        await Actor.set_status_message(msg)


if __name__ == "__main__":
    asyncio.run(main())
