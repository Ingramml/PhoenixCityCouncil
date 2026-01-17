# Scraping Performance Optimization Recommendations

This document outlines potential improvements to speed up the Phoenix City Council data scraping process.

---

## Current Performance Baseline

| Phase | Current Time | Bottlenecks |
|-------|--------------|-------------|
| API calls | ~2 min | Minimal - already efficient |
| Website scraping | 30-60 min | Multiple sleep calls, sequential processing |
| Video links | ~10 min | Manual process |

**Primary time consumers in `fetch_2024_data_enhanced.py`:**
- `time.sleep(2)` after page load (line 140)
- `time.sleep(3)` waiting for dynamic content (line 213)
- `time.sleep(0.8)` after each popup click (line 229)
- `time.sleep(0.3)` after popup close (line 250, 254)
- `time.sleep(1)` between meetings (line 576)
- Sequential processing of Action Details popups
- Individual item summary scraping requires page navigation for each item

---

## Optimization Categories

### 1. Reduce Sleep Times (Quick Win - 30-50% faster)

**Current delays vs. recommended:**

| Location | Current | Recommended | Savings |
|----------|---------|-------------|---------|
| After page load | `time.sleep(2)` | `time.sleep(0.5)` + wait_for_selector | ~1.5s/meeting |
| Dynamic content wait | `time.sleep(3)` | Use `wait_for_selector` | ~2s/meeting |
| After popup click | `time.sleep(0.8)` | `time.sleep(0.3)` + wait | ~0.5s/popup |
| After popup close | `time.sleep(0.3)` | `time.sleep(0.1)` | ~0.2s/popup |
| Between meetings | `time.sleep(1)` | `time.sleep(0.3)` | ~0.7s/meeting |

**Implementation:**
```python
# Instead of:
self.page.goto(meeting_url, wait_until="networkidle", timeout=60000)
time.sleep(2)

# Use:
self.page.goto(meeting_url, wait_until="domcontentloaded", timeout=30000)
self.page.wait_for_selector("table tr", timeout=10000)
# No additional sleep needed
```

**Estimated savings:** 15-20 minutes for Q1 2024 data

---

### 2. Parallel API Calls (Moderate - 20-30% faster)

**Current:** Sequential API calls for each meeting's items
```python
for event in events:
    items = get_event_items(event_id)  # Waits for response
```

**Optimized:** Use `concurrent.futures` for parallel requests
```python
import concurrent.futures

def fetch_all_event_items(events):
    """Fetch all event items in parallel."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(get_event_items, e.get("EventId")): e
            for e in events
        }
        results = {}
        for future in concurrent.futures.as_completed(futures):
            event = futures[future]
            results[event.get("EventId")] = future.result()
    return results
```

**Estimated savings:** 30-60 seconds for API phase

---

### 3. Batch Popup Processing (Major - 40-60% faster)

**Current:** Click popup → wait → extract → close → repeat
```python
for link in action_detail_links:
    link.click()
    time.sleep(0.8)
    votes = self._extract_votes_from_popup()
    close_btn.click()
    time.sleep(0.3)
```

**Optimized Option A:** Use JavaScript to extract all data at once
```python
def _extract_all_votes_via_js(self):
    """Extract all vote data using JavaScript without clicking popups."""
    # The vote data might be available in the page's JavaScript variables
    # or can be extracted from data attributes
    script = """
    () => {
        const results = {};
        // Find all Action details links and their associated data
        document.querySelectorAll('a[href*="ActionDetail"]').forEach(link => {
            const row = link.closest('tr');
            const fileNum = row?.querySelector('td:first-child a')?.textContent?.trim();
            const href = link.getAttribute('href');
            // Extract ID from href and store for API lookup
            const match = href?.match(/ID=(\\d+)/);
            if (match && fileNum) {
                results[fileNum] = match[1];
            }
        });
        return results;
    }
    """
    return self.page.evaluate(script)
```

**Optimized Option B:** Open multiple tabs for parallel popup extraction
```python
def _scrape_votes_parallel(self, popup_urls):
    """Open multiple popups in parallel tabs."""
    pages = []
    for url in popup_urls[:5]:  # Process 5 at a time
        page = self.browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        pages.append(page)

    # Extract from all pages
    results = []
    for page in pages:
        votes = self._extract_votes_from_page(page)
        results.append(votes)
        page.close()

    return results
```

**Estimated savings:** 10-20 minutes for Q1 2024 data

---

### 4. Skip Unnecessary Data (Quick Win - 10-20% faster)

**Current:** Scrapes ALL agenda items including headers and informational items

**Optimized:** Filter to only items with votes
```python
# Skip items that don't have votes
if not item.get("EventItemPassedFlag") and not item.get("EventItemTally"):
    # This is likely a header or informational item
    continue

# Skip consent items that don't need individual votes
if item.get("EventItemConsent") == 1:
    # Use "Consent" for all members, no popup needed
    continue
```

**Estimated savings:** 5-10 minutes (skips ~30% of items)

---

### 5. Cache Vote Data (Quick Win for repeat runs)

**Current:** Re-scrapes everything on each run

**Optimized:** Cache scraped data to JSON
```python
import json
import os

CACHE_FILE = "vote_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def scrape_meeting_with_cache(meeting_url, meeting_date):
    cache = load_cache()
    if meeting_date in cache:
        print(f"  Using cached data for {meeting_date}")
        return cache[meeting_date]

    # Scrape as usual
    data = scraper.scrape_meeting(meeting_url)

    # Cache the result
    cache[meeting_date] = data
    save_cache(cache)
    return data
```

**Estimated savings:** 90%+ on repeat runs

---

### 6. Use Legistar API for Roll Calls (Alternative approach)

**Discovery:** The API has a roll calls endpoint that might have vote data

```python
def get_roll_calls_for_item(event_item_id):
    """Get roll call votes from API instead of scraping."""
    url = f"{BASE_URL}/eventitems/{event_item_id}/rollcalls"
    return fetch_json(url) or []
```

**Note:** Current testing shows this returns attendance (Present/Absent) not item votes (Yes/No). But worth re-testing for different item types.

---

### 7. Reduce Page Navigation (Major - 30-40% faster)

**Current:** When scraping summaries, navigates away then back:
```python
item_summary = scraper.scrape_item_summary(detail_url)
# Navigate back to meeting page for next item
scraper.page.goto(meeting_url, wait_until="networkidle", timeout=60000)
```

**Optimized Option A:** Open summary pages in new tabs
```python
def scrape_item_summary_in_new_tab(self, detail_url):
    """Scrape summary in a new tab without leaving current page."""
    new_page = self.browser.new_page()
    try:
        new_page.goto(detail_url, wait_until="domcontentloaded", timeout=15000)
        summary = self._extract_summary_from_page(new_page)
        return summary
    finally:
        new_page.close()
```

**Optimized Option B:** Collect all URLs, batch process at end
```python
def scrape_all_summaries_batch(self, detail_urls):
    """Process all summary URLs after collecting votes."""
    summaries = {}
    for file_num, url in detail_urls.items():
        self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
        summaries[file_num] = self._extract_summary()
        time.sleep(0.2)  # Minimal delay
    return summaries
```

**Estimated savings:** 10-15 minutes when using `--scrape-summaries`

---

### 8. Use Faster Wait Strategies

**Current:** `wait_until="networkidle"` waits for ALL network activity to stop

**Optimized:** Use more specific waits
```python
# Instead of waiting for all network to be idle:
self.page.goto(url, wait_until="networkidle", timeout=60000)

# Wait only for the content we need:
self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
self.page.wait_for_selector("table.rgMasterTable", timeout=10000)
```

| Wait Strategy | Speed | Reliability |
|---------------|-------|-------------|
| `networkidle` | Slowest | Most reliable |
| `load` | Medium | Good |
| `domcontentloaded` | Fast | Usually sufficient |
| `commit` | Fastest | May miss dynamic content |

---

### 9. Browser Optimization Settings

**Add performance-focused browser launch options:**
```python
def start(self, headless=True):
    self.playwright = sync_playwright().start()
    self.browser = self.playwright.chromium.launch(
        headless=headless,
        args=[
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-images',  # Don't load images
            '--blink-settings=imagesEnabled=false'
        ]
    )
    # Create context with optimized settings
    self.context = self.browser.new_context(
        java_script_enabled=True,
        ignore_https_errors=True,
        viewport={'width': 1280, 'height': 720}
    )
    self.page = self.context.new_page()

    # Block unnecessary resources
    self.page.route("**/*.{png,jpg,jpeg,gif,svg,ico}", lambda route: route.abort())
    self.page.route("**/*.css", lambda route: route.abort())  # Optional
```

**Estimated savings:** 10-20% overall

---

## Implementation Priority

| Priority | Optimization | Effort | Impact | Risk |
|----------|--------------|--------|--------|------|
| 1 | Reduce sleep times | Low | High | Low |
| 2 | Skip unnecessary items | Low | Medium | Low |
| 3 | Faster wait strategies | Low | Medium | Medium |
| 4 | Browser optimization | Low | Medium | Low |
| 5 | Cache vote data | Medium | High* | Low |
| 6 | Parallel API calls | Medium | Low | Low |
| 7 | Batch popup processing | High | High | Medium |
| 8 | New tab for summaries | Medium | Medium | Low |

*High impact on repeat runs only

---

## Quick Implementation: Optimized Sleep Times

Here's a minimal change that could be applied immediately:

```python
# In scrape_meeting():
self.page.goto(meeting_url, wait_until="domcontentloaded", timeout=30000)
self.page.wait_for_selector("table tr", timeout=10000)
# Remove: time.sleep(2)

# In _scrape_all_action_details():
self.page.wait_for_selector("table tr", timeout=10000)
# Remove: time.sleep(3)

# After popup click:
link.click()
self.page.wait_for_selector("dialog, [role='dialog'], .RadWindow", timeout=5000)
# Remove: time.sleep(0.8)

# After popup close:
close_btn.click(timeout=2000)
time.sleep(0.1)  # Reduced from 0.3

# Between meetings:
time.sleep(0.3)  # Reduced from 1
```

---

## Expected Results After Optimization

| Phase | Current | After Basic Opt | After Full Opt |
|-------|---------|-----------------|----------------|
| API calls | 2 min | 1.5 min | 1 min |
| Website scraping | 45 min | 25-30 min | 15-20 min |
| Video links | 10 min | 10 min | 5 min* |
| **Total** | **~60 min** | **~40 min** | **~25 min** |

*If automated Phoenix.gov scraping is fixed

---

## Testing Recommendations

1. **Benchmark current performance:**
   ```bash
   time python fetch_2024_data_enhanced.py --start-month 1 --end-month 2
   ```

2. **Test each optimization individually** to measure impact

3. **Monitor for failures** - faster isn't better if it breaks reliability

4. **Consider a `--fast` flag** for development vs. production modes:
   ```python
   if args.fast:
       POPUP_WAIT = 0.3
       PAGE_WAIT = 0.5
   else:
       POPUP_WAIT = 0.8
       PAGE_WAIT = 2
   ```
