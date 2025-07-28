from __future__ import annotations

import asyncio, json, os, sys, re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

from pydantic import BaseModel, Field
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
    LLMConfig,
)

# ── Pydantic models ──────────────────────────────────────────────────────────
class ProductLink(BaseModel):
    url: str
    price: Optional[str] = None
    store: Optional[str] = None
    rating: Optional[str] = None


class Product(BaseModel):
    rank: int
    name: str
    price: Optional[str] = None
    rating: Optional[str] = None
    reviews_count: Optional[str] = None
    links: List[ProductLink] = Field(default_factory=list)


class ShoppingResults(BaseModel):
    query: str
    total_products: int
    products: List[Product]
    scraped_at: str
    search_url: str


# ── Constants & selectors ────────────────────────────────────────────────────
LLM_MODEL = "openai/gpt-4.1-nano"
MAX_CARDS = 50
SCHEMA_PATH = Path("gshop_sidebar_schema.json")

CARD_JS = "div.njFjte"
SIDEBAR_ROOT = "div.zxYWDc.q9kVJb"
SIDEBAR_TITLE = f'{SIDEBAR_ROOT} [data-attrid="product_title"]'

SAMPLE_HTML = """<div class="bi9tFe PZPZlf pb3iw" jsname="ZOnBqe" aria-level="2" autofocus="true" data-attrid="product_title" role="heading" tabindex="-1">Logitech G PRO X Wireless Lightspeed Gaming Headset</div>\n<span class="dGP1Db PZPZlf Dh6lu yoARA Y0A0hc" data-enable-scroll="true" role="link" tabindex="0" jsaction="click:trigger.MAWWy" data-attrid="product_rating"><span class="yi40Hd YrbPuc" aria-hidden="true">4.4</span><span class="z3HNkc" aria-label="Rated 4.4 out of 5," role="img"><span aria-hidden="true"><span class="gTPtFb" style="background:linear-gradient(to right, currentcolor 62px, #80868b 0%);"></span></span></span><span class="RDApEe YrbPuc">(<span class="Bk5Fre">2.9K user reviews</span>)</span></span>\n<div class="PshwNb"><a data-hveid="155" data-ved="0CJsBEI_yBGoXChMI-K6zjOfdjgMVAAAAAB0AAAAAEDY" href="https://www.logitechg.com/en-us/products/gaming-audio/pro-x-wireless-headset.981-000906.html?utm_source=google&amp;gPromoCode=LOGIGUS26MJUL30PERCENTOFF&amp;gQT=1" ping="/url?sa=i&amp;source=web&amp;cd=&amp;ved=0CJsBEI_yBGoXChMI-K6zjOfdjgMVAAAAAB0AAAAAEDY&amp;url=https%3A%2F%2Fwww.logitechg.com%2Fen-us%2Fproducts%2Fgaming-audio%2Fpro-x-wireless-headset.981-000906.html%3Futm_source%3Dgoogle%26gPromoCode%3DLOGIGUS26MJUL30PERCENTOFF%26gQT%3D1&amp;psig=AOvVaw0zlFZ2M5ta36sWot8EtyvS&amp;ust=1753732040317881&amp;opi=95576897" class="P9159d hMk97e BbI1ub" jsname="wN9W3" rel="noopener" target="_blank"><div><div class="shi3lc"><div class="VYi4ab Y7glZ"><span>Most popular</span></div></div><div class="keF4Wd b8zvM"><div class="uXJVPd gfKE6c"><div class="EHWXMb RLo00b"><div class="Ncoygd"><div class="EHWXMb j6sxFe"><div class="EHWXMb"><div class="tLevwc"><g-img class="ZGomKf" aria-hidden="true"><img class="zr758c YQ4gaf" style="border-radius:0 0 0 0;" id="dimg_4628" src="https://encrypted-tbn0.gstatic.com/faviconV2?url=https://www.logitechg.com&amp;client=SHOPPING&amp;size=32&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL" height="16" width="16" alt=""></g-img></div><div class="hP4iBf gUf0b uWvFpd" data-report-feedback-about-context="Logitech G">Logitech G</div></div></div></div><div class="QcEgce qUbqne WbrF3c"><div class="HDOUoe v0gWi"><div class="Ak8wjc"></div><div class="GBgquf JIep9e"><span aria-label="Current price: $179.99">$179.99</span></div></div></div></div><div></div><div></div><div class="Rp8BL CpcIhb y1FcZd rYkzq">Logitech G PRO X Wireless Gaming Headset with Blue VO!CE in Black</div><div><div class="NV5awf AiiGt"><div class="OaQPmf rArxUc"><span class="gASiG"><span class="gASiG jvP2Jb jIpmhc"><span>In stock online</span></span></span></div><div class="OaQPmf Z8dN6c"><span class="gASiG"><span class="gASiG" aria-label="Rated 3.4 out of 5." role="img"><span class="CXkihc z1asCe" style="height:16px;line-height:16px;width:16px;" aria-hidden="true"><svg focusable="false" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"></path></svg></span><span class="NFq8Ad cHaqb" aria-hidden="true">3.4/5</span></span></span></div><div class="OaQPmf Z8dN6c"><span class="Wvm8Ob" aria-hidden="true">·</span><span class="gASiG"><span class="gASiG" aria-label="Free delivery from August 2 to 7" role="img"><span aria-hidden="true">Free delivery Aug 2 – 7</span></span></span></div><div class="OaQPmf Z8dN6c"><span class="Wvm8Ob" aria-hidden="true">·</span><span class="gASiG"><span class="gASiG"><span>Free 30-day returns</span></span></span></div><div class="OaQPmf Z8dN6c"><span class="Wvm8Ob" aria-hidden="true">·</span><span class="gASiG"><span class="gASiG aZosn"><span>Buy 3, Save 30%</span></span></span></div></div></div></div></div></div></a></div>
"""


# ── JavaScript helpers ───────────────────────────────────────────────────────
def js_cfg(js: str, session: str, wait_css: str | None = None) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        session_id=session,
        js_only=True,
        js_code=js,
        wait_for=f"css:{wait_css}" if wait_css else None,
    )

NEXT_TILE_JS = f"""
(() => {{
    const tiles = Array.from(document.querySelectorAll('{CARD_JS}'));
    const next  = tiles.find(t => !t.dataset.done);
    if (!next) return 'NO_CARD';
    next.dataset.done = '1';
    next.style.outline = '3px solid red';
    next.scrollIntoView({{block:'center'}});
    next.click();
    return 'OK';
    }})();
"""

SCROLL_JS = "window.scrollBy(0, window.innerHeight);"

# ── Schema cache / generator ────────────────────────────────────────────────
TARGET_FIELDS = {"product_title", "overall_rating", "review_count",
                 "store", "price", "href", "store_rating"}

def generate_sidebar_schema(sample_html: str, out_path: Path, *, force: bool = False) -> dict:
    """Generate (or load) the sidebar schema, verifying required fields."""
    if out_path.exists() and not force:
        schema = json.loads(out_path.read_text())
    else:
        schema = JsonCssExtractionStrategy.generate_schema(
            html=sample_html,
            llm_config=LLMConfig(provider=LLM_MODEL, api_token=os.getenv("LLM_KEY")),
            query=(
                "Extract the following:\n"
                "• product_title  – text at data-attrid='product_title'\n"
                "• overall_rating – numeric rating inside data-attrid='product_rating'\n"
                "• review_count   – text like “6.1K user reviews” inside same block\n"
                "• merchants      – LIST of rows, each row has:\n"
                "    • store        – text in div.hP4iBf\n"
                "    • price        – span whose aria-label starts with 'Current price'\n"
                "    • href         – href attribute of the row’s outer <a>\n"
                "    • store_rating – span whose aria-label starts with 'Rated'\n"
                "Return a JSON/CSS schema that captures **only** those fields."
            ),
        )
        out_path.write_text(json.dumps(schema, indent=2))

    _validate_schema(schema)
    print(f"GENERATED SCHEMA:\n{schema}")
    return schema


def _validate_schema(schema: dict) -> None:
    """Fail fast if the schema is missing any required field names."""
    names = {f["name"] for f in schema["fields"]}
    for f in schema["fields"]:
        if f["type"] == "list":
            names.update({sub["name"] for sub in f["fields"]})

    missing = TARGET_FIELDS - names
    if missing:
        raise ValueError(
            f"Generated schema is missing fields: {', '.join(sorted(missing))}"
        )

# ── Main coroutine ───────────────────────────────────────────────────────────
async def scrape_google_shopping(query: str) -> ShoppingResults:
    search_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(query)}"
    session_id = "gshop"
    products: List[Product] = []

    css_strategy = JsonCssExtractionStrategy(schema=json.loads(SCHEMA_PATH.read_text()))

    async with AsyncWebCrawler(config=BrowserConfig(headless=False, verbose=True)) as crawler:
        # open page
        await crawler.arun(
            url=search_url,
            config=CrawlerRunConfig(session_id=session_id, wait_for=f"css:{CARD_JS}"),
        )

        # lazy-scroll
        for _ in range(6):
            await crawler.arun(url=search_url, config=js_cfg(SCROLL_JS, session_id))

        # iterate tiles
        for i in range(MAX_CARDS):
            click = await crawler.arun(
                url=search_url,
                config=js_cfg(NEXT_TILE_JS, session_id, wait_css=SIDEBAR_TITLE),
            )
            if click.extracted_content == "NO_CARD":
                break

            res = await crawler.arun(
                url=search_url,
                config=CrawlerRunConfig(
                    session_id=session_id,
                    js_only=True,
                    css_selector=SIDEBAR_ROOT,
                    extraction_strategy=css_strategy,
                ),
            )
            if not res.success:
                continue

            rows = res.extracted_content if isinstance(res.extracted_content, list) \
                                         else json.loads(res.extracted_content)
            if not rows:
                continue

            # global fields from first row
            title   = rows[0].get("product_title")
            rating  = rows[0].get("overall_rating")
            reviews = rows[0].get("review_count")

            links: List[ProductLink] = []
            for m in rows[0].get("merchants", []):
                links.append(
                    ProductLink(
                        url   = m.get("href"),
                        price = m.get("price"),
                        store = m.get("store"),
                        rating= m.get("store_rating"),
                    )
                )

            products.append(
                Product(
                    rank=len(products) + 1,
                    name=title,
                    price=rows[0].get("price"),
                    rating=rating,
                    reviews_count=reviews,
                    links=links,
                )
            )

    return ShoppingResults(
        query=query,
        total_products=len(products),
        products=products,
        scraped_at=datetime.now(timezone.utc).isoformat(),
        search_url=search_url,
    )


def slugify(text: str) -> str:
    """Make a safe filename slug from the query string."""
    return re.sub(r"[^\w.-]", "_", text).strip("_").lower()

def save_results(results: ShoppingResults, *, folder: Path = Path("scrapes")) -> Path:
    folder.mkdir(exist_ok=True)
    stamp   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname   = f"gshop_{slugify(results.query)}_{stamp}.json"
    outpath = folder / fname
    outpath.write_text(results.model_dump_json(indent=2))
    return outpath



# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "LLM_KEY" not in os.environ:
        sys.exit("❌  Set LLM_KEY")

    # uncomment below to generate the schema into a json file. make sure to edit the baseSelector to be the correct root selector
    # generate_sidebar_schema(sample_html=SAMPLE_HTML, out_path=SCHEMA_PATH)
    query = input("🔍 Google Shopping search term: ").strip()
    if not query:
        sys.exit("No query given — exiting.")
    out = asyncio.run(scrape_google_shopping(query))
    path = save_results(out)
    print(f"✅  Saved to {path}")