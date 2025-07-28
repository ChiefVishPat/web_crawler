# Google-Shopping LLM Scraper

Fetch structured product data from Google Shopping with **one command**.  
The script leverages the crawl4ai library lets GPT‑4 generate a sidebar‑HTML schema, and exports clean JSON.

## Demo Video
https://www.loom.com/share/d87f88f6918a48b2b121e1afcc40b761?sid=c79fd8be-d9a6-4a1a-87aa-2337cfe15b70
<div>
    <a href="https://www.loom.com/share/d87f88f6918a48b2b121e1afcc40b761">
      <p>Automating Product Data Scraping from Google Shopping 🛍️ - Watch Video</p>
    </a>
    <a href="https://www.loom.com/share/d87f88f6918a48b2b121e1afcc40b761">
      <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/d87f88f6918a48b2b121e1afcc40b761-1028778a17d3dbb5-full-play.gif">
    </a>
  </div>

## Quick start
```bash
# create & activate a uv virtual‑env
uv venv .venv

# install runtime deps
uv add crawl4ai pydantic

# set your LLM key
export LLM_KEY=""
```

## Running
```bash
uv run llm_scraper.py            # prompts for query interactively
```

### First‑run caveat → manual tweak
On the first query the script asks gpt-4.1-nano to infer a JSON/CSS schema and saves it to **gshop_sidebar_schema.json**.  
Google’s markup drifts, so GPT may guess a wrong root selector. Open the file once and set
```json
"baseSelector": "div.zxYWDc.q9kVJb"
```
You might need to change the div tag to a new one. You can do this by clicking on a product card, inspect element and select the sideview container (shown in the video)

After this one‑time fix every run re‑uses the cached schema—no extra tokens.

Example (truncated):
```json
{
  "query": "top gaming headsets",
  "total_products": 28,
  "scraped_at": "2025-07-28T09:30:15Z",
  "search_url": "https://www.google.com/…",
  "products": [
    {
      "rank": 1,
      "name": "Logitech G ASTRO A50 X Gaming Headset",
      "price": "$339.98",
      "rating": "4.5",
      "reviews_count": "846 user reviews",
      "links": [
        {
          "url": "https://www.gamestop.com/…",
          "price": "$339.98",
          "store": "GameStop",
          "rating": "4.4/5"
        },
        {
          "url": "https://www.bestbuy.com/…",
          "price": "$399.99",
          "store": "Best Buy",
          "rating": "4.6/5"
        }
      ]
    }
  ]
}
```

## Use‑cases
| Use‑case | What you can do |
|----------|-----------------|
| Price monitoring | Track daily price & stock across merchants |
| MAP / compliance | Alert when partners under‑cut allowed pricing |
| Affiliate feeds  | Generate deeplink CSVs for SEO pages |
| Market research  | Snapshot ratings & review volumes in any vertical |
| LLM content      | Feed JSON to GPT‑4o → auto‑write buying guides |

## Next steps
* Split library/CLI so you can `import scrape_google_shopping()`
* Improve the scraper to scrape ChatGPT website
* Implement IP/Proxy rotation
