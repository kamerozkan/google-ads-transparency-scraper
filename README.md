# Google Ads Transparency Center Scraper & Spy API

[![Run on Apify](https://apify.com/actor-badge?actor=kamerozkan/google-ads-transparency-scraper)](https://apify.com/kamerozkan/google-ads-transparency-scraper)
[![Pricing](https://img.shields.io/badge/Pricing-Pay--Per--Event%20($0.0015)-blue)](https://apify.com/kamerozkan/google-ads-transparency-scraper)
[![Memory](https://img.shields.io/badge/Memory-512%20MB-green)](https://apify.com/kamerozkan/google-ads-transparency-scraper)
[![Speed](https://img.shields.io/badge/Speed-1.3s%20per%20query-success)](https://apify.com/kamerozkan/google-ads-transparency-scraper)

Extract verified commercial advertisements from the **Google Ads Transparency Center** programmatically without browser overhead, slow rendering, or Google account requirements.

Search by **domain name** (`nike.com`), **brand name** (`Nike`), or verified **Advertiser ID** (`AR...`) to uncover active ad creatives, formats, image URLs, active campaign durations, and destination links.

---

## Why Google Ads Transparency Scraper?

| Feature | This Actor (kamerozkan) | Traditional Ad Spy Tools (AdSpy, BigSpy) | Playwright / Puppeteer Scrapers |
| :--- | :--- | :--- | :--- |
| **Pricing Model** | **$0.0015 / creative (Pay only for what you scrape)** | $149 - $299 / month fixed | High compute costs ($0.05 / run) |
| **Speed** | **1.3 seconds (Direct RPC Protocol)** | Dashboard search only | 30 - 60 seconds (Heavy Chrome) |
| **Google Login** | **Not Required (Anonymous)** | Account dependent | Often triggers Google Captcha |
| **API Integration** | **Direct REST API & Webhooks** | No native API (UI only) | Complex infrastructure needed |
| **Creative Formats** | **IMAGE, TEXT, VIDEO, or ALL** | Limited filtering | Brittle DOM selectors |
| **Active Duration** | **First Seen, Last Seen & Days Active** | Rough estimates | Manual parsing |

---

## Core Use Cases

- **Competitor Ad Intelligence & Creative Benchmarking:** Monitor competitors' active ad creatives, visual design trends, and seasonal promotional angles.
- **Winning Creative Discovery:** Filter ads by `daysActive > 60` to immediately identify evergreen, profitable ad creatives that competitors keep running.
- **PPC & Media Buying Audits:** Verify whether prospective clients or target brands are actively investing in Google Display, Search, or YouTube campaigns.
- **Brand Protection & Trademark Monitoring:** Detect unauthorized vendors, resellers, or counterfeiters bidding on your brand's trademarked domains and keywords.
- **AI Ad Analysis Pipelines:** Feed extracted ad headlines, images, and copy into LLM pipelines (OpenAI, Claude, Gemini) for automated competitor messaging breakdown.

---

## Key Features

- **Direct Internal Protocol Engine:** Connects straight to Google Ads Transparency Center backend endpoints without headless browsers. 10x faster and 90% cheaper in compute.
- **Flexible Entity Resolution:** Search by domain (`shopify.com`), brand name (`Shopify`), or exact Advertiser ID (`AR...`).
- **Format Filtering:** Target specific creative types: `"ALL"`, `"IMAGE"`, `"TEXT"`, or `"VIDEO"`.
- **Comprehensive Ad Metadata:**
  - Creative ID (`CR...`) & Advertiser ID (`AR...`)
  - Verified Advertiser entity name & domain
  - High-resolution Image CDN URLs
  - First Seen Date, Last Seen Date, and Total Days Active
  - Canonical Google Ads Transparency Center verification URL
- **Pay-Per-Result Pricing:** Pay only $0.0015 per ad creative. Zero wasted subscription fees.

---

## Input Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `queries` | Array of Strings | **Yes** | `["nike.com"]` | List of domains, brands, or Advertiser IDs (`AR...`) to scrape. |
| `format` | String | No | `"ALL"` | Ad format filter: `"ALL"`, `"IMAGE"`, `"TEXT"`, or `"VIDEO"`. |
| `maxAdsPerQuery` | Integer | No | `40` | Maximum number of ads to collect per query (1 to 1,000). |
| `maxConcurrency` | Integer | No | `5` | Simultaneous search threads running in parallel. |
| `proxyConfiguration` | Object | No | `{ "useApifyProxy": true }` | Apify Datacenter or Residential proxy settings. |

---

## Example JSON Output

Each record represents one verified ad creative:

```json
{
  "query": "nike.com",
  "advertiserId": "AR11604595304388132865",
  "advertiserName": "NIKE EUROPEAN OPERATIONS NETHERLANDS B.V.",
  "creativeId": "CR12345678901234567890",
  "format": "IMAGE",
  "imageUrl": "https://tpc.googlesyndication.com/simgad/123456789...",
  "firstSeen": "2026-08-01",
  "lastSeen": "2026-10-06",
  "daysActive": 66,
  "adUrl": "https://adstransparency.google.com/advertiser/AR11604595304388132865/creative/CR12345678901234567890",
  "scrapedAt": "2026-10-06T19:33:14+00:00"
}
```

---

## Code Examples

### Python (apify-client)

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_API_TOKEN")

run_input = {
    "queries": ["shopify.com", "stripe.com"],
    "format": "IMAGE",
    "maxAdsPerQuery": 20,
}

# Run the Actor and wait for completion
run = client.actor("kamerozkan/google-ads-transparency-scraper").call(run_input=run_input)

# Fetch ad records from dataset
for ad in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"[{ad['advertiserName']}] {ad['format']} ad active for {ad['daysActive']} days: {ad['adUrl']}")
```

### JavaScript / Node.js (apify-client)

```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({
    token: 'YOUR_APIFY_API_TOKEN',
});

const runInput = {
    queries: ['airbnb.com'],
    format: 'ALL',
    maxAdsPerQuery: 50,
};

const run = await client.actor('kamerozkan/google-ads-transparency-scraper').call(runInput);
const { items } = await client.dataset(run.defaultDatasetId).listItems();

console.log(`Extracted ${items.length} competitor ads:`, items);
```

### cURL

```bash
curl --request POST \
  --url "https://api.apify.com/v2/acts/kamerozkan~google-ads-transparency-scraper/runs?token=YOUR_APIFY_API_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{
    "queries": ["nike.com"],
    "format": "IMAGE",
    "maxAdsPerQuery": 30
  }'
```

---

## Pricing Details

This Actor operates under **Pay-Per-Event (PPE)**:
- **Per Scraped Ad Creative ($0.0015):** Charged only for successfully extracted ad creative records.
- 1,000 ad creatives cost just $1.50 (compared to $150+/month for legacy spy subscriptions).
- Platform compute usage is fully included in the event fee.

---

## Related Apify Intelligence & Scraping Tools

- [Google Hotels Prices & OTA Rate Tracker API](https://apify.com/kamerozkan/google-hotels-prices) - Real-time hotel rates, room types, and OTA rate disparity scraper.
- [Google Flights Prices & Fare Tracker API](https://apify.com/kamerozkan/google-flights-prices) - Real-time flight fares, non-stop routes, and multi-airline price tracking.
- [AI Brand Visibility & GEO Rank Tracker API](https://apify.com/kamerozkan/ai-brand-visibility-tracker) - Track brand mentions, Share of Voice (SOV), and citations across ChatGPT, Perplexity, Gemini, and Claude.
