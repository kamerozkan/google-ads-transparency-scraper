# Google Ads Transparency Center Scraper & Spy API

Extract verified advertisements from the **Google Ads Transparency Center** programmatically without browser overhead, slow rendering, or login requirements.

Search by **domain name**, **brand**, or **Google Advertiser ID** to uncover active ad creatives, formats, image URLs, active campaign durations, and destination links.

---

## Features

- **Direct RPC Protocol Engine:** Connects straight to Google's internal APIs. No heavy Puppeteer/Playwright browsers. Up to 10x faster and 90% cheaper in compute than browser-based scrapers.
- **Multiple Search Options:** Search directly by domain (`nike.com`), brand name (`Nike`), or verified Advertiser ID (`AR...`).
- **Format Filtering:** Filter by **IMAGE**, **TEXT**, or **VIDEO**, or retrieve all formats in a single run.
- **Rich Campaign Intelligence:**
  - Unique Ad Creative ID (`CR...`) & Advertiser ID (`AR...`)
  - Verified Advertiser entity name & domain
  - Direct Image CDN URLs (for image and banner creatives)
  - First Seen Date, Last Seen Date, and Total Days Active
  - Direct link to the canonical Google Ads Transparency Center ad page
  - Decoded ad headline and destination landing page URL when available
- **Cursor-based Pagination:** Seamlessly paginate through hundreds or thousands of ads per advertiser.
- **Pay-Per-Result Pricing:** Pay only for the ad creatives you extract ($0.0015 / ad). No wasteful hourly compute charges.

---

## Use Cases

- **Competitor Ad Intelligence:** Monitor competitors' active ads, ad copy angles, and creative visual styles.
- **Ad Creative Spy & Benchmarking:** See which creatives have been running the longest (`daysActive > 100`) to identify your competitors' winning ad designs.
- **Media Buying & PPC Audits:** Verify whether prospective clients or competitors are actively spending on Google Display, Search, or YouTube.
- **Brand Protection & Trademark Monitoring:** Detect unauthorized vendors or counterfeiters bidding on your brand's keywords and domains.

---

## Input Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `queries` | Array of Strings | **Yes** | `["nike.com"]` | List of domains, brands, or Advertiser IDs (`AR...`) to scrape. |
| `format` | String | No | `"ALL"` | Ad format filter: `"ALL"`, `"IMAGE"`, `"TEXT"`, or `"VIDEO"`. |
| `maxAdsPerQuery` | Integer | No | `40` | Maximum number of ads to collect per query (1 to 1,000). |
| `maxConcurrency` | Integer | No | `5` | Number of simultaneous searches running in parallel. |
| `proxyConfiguration` | Object | No | `{ "useApifyProxy": true }` | Apify Datacenter or Residential proxy configuration. |

### Example Input

```json
{
  "queries": [
    "shopify.com",
    "airbnb.com"
  ],
  "format": "ALL",
  "maxAdsPerQuery": 50,
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

---

## Output Data Structure

The Actor pushes structured ad creative objects to the default Apify Dataset:

```json
{
  "creativeId": "CR04866772011696783361",
  "advertiserId": "AR15908226811872411649",
  "advertiserName": "Airbnb, Inc.",
  "targetDomain": "airbnb.com",
  "format": "IMAGE",
  "firstShown": "2025-09-24T12:24:59+00:00",
  "lastShown": "2026-10-06T19:10:21+00:00",
  "daysActive": 377.3,
  "imageUrl": "https://tpc.googlesyndication.com/archive/simgad/11454630275221382409",
  "transparencyUrl": "https://adstransparency.google.com/advertiser/AR15908226811872411649/creative/CR04866772011696783361?region=anywhere"
}
```

---

## Pricing

This Actor operates on the **Pay-per-event** pricing model:

- **$0.0015** per scraped ad creative.
- **Compute:** Extremely lightweight (runs on 512 MB memory), incurring virtually zero compute overhead.

---

## Privacy & Legal

This Actor extracts only publicly accessible data from the Google Ads Transparency Center, provided by Google under global transparency regulations. It is an independent tool and is not affiliated with or endorsed by Google LLC.
