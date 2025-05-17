# POAP: An End-to-end Public Opinion Analysis Pipeline for Weibo

**POAP** is a fully automated pipeline for analyzing public opinion on Sina Weibo. Provide a single natural language query with three key parameters—**keywords**, **date** (`YYYY-MM-DD`), and **platform (Sina Weibo)**—POAP will run an automated end-to-end analysis workflow, producing a detailed analysis report with **no further manual steps**.


## 🛠️ System Overview

POAP is organized into four agents:

1. **Agent 0: Coordinator (with embedded Weibo Crawler)**  
   - **Coordinator** parses user query to extract `event_keywords`, `start_datetime`,  end_datetime`, and `platform` (currently only Sina Weibo).  
   - **Weibo Crawler** (an internal tool of Agent 0) fetches Weibo **posts** by iterating hourly.   
   - **Limitation:** The built-in crawler only supports **Sina Weibo** and captures data for one **24-hour period** per invocation. To collect data across multiple days, manually call `run_weibo_crawl(...)` for each date.  
   - **Before first run**, obtain and update your Weibo login cookie in `WeiboCrawler.py` (see below).

2. **Agent 2: Sentiment Analysis**  
   - Automatically reads the crawler collected data CSV and labels each post as positive, neutral, or negative, writing `sentiment_analysis_output.csv`.

3. **Agent 3: Topic Extraction**  
   - Automatically reads the crawler collected data CSV and extracts key discussion topics via keyword clustering and frequency analysis, writing `topic_modelling_output.csv`.

4. **Agent 4: Report Generation**  
   - Merges the sentiment and topic CSVs, computes aggregated topic–sentiment statistics, surfaces emergent insights (e.g. topics with spikes in negative sentiment), and outputs a human-readable report to the console or notebook.

> **Note:** After your single query input, POAP runs fully automatically and returns the final report without any further manual intervention.

## 📁 Project Structure

```text
.
├── Agents.py                        # Agent 0 (Coordinator + embedded crawler) and Agents 2–4
├── WeiboCrawler.py                  # Crawler logic (internal to Agent 0)
├── utils.py                         # CLI & workflow helpers (conversation_loop, step functions)
├── AutoPublicOpinionAnalysist.ipynb # Jupyter demo notebook with inline outputs
├── prompts/                         # System-prompt templates for each agent
│   ├── Coordinator_prompt.txt
│   ├── Sentiment_analysist_prompt.txt
│   ├── Topic_modelling_prompt.txt
│   └── Summarizer_*.txt
├── requirements.txt                 # Python dependencies
└── POAP.png                         # Concept diagram


## 🔧 Configuring the Weibo Crawler

Before running the pipeline, obtain your Weibo login cookie and update the `headers['cookie']` field in **WeiboCrawler.py**:

1. In your browser, log into Weibo with your account.  
2. Right-click the page and select **Inspect** (or press `F12`).  
3. Go to the **Network** tab and refresh the page.  
4. Scroll the list of requests until you see a request to a Weibo endpoint (e.g., `www.weibo.com`, `sinaimg.cn`). You may need to scroll further to load more entries.  
5. Click on one request and switch to the **Headers** panel on the right.  
6. Under **Request Headers**, locate and copy the entire **Cookie** value.  
7. In `WeiboCrawler.py` (around line 27), replace the `cookie` field in the `headers` dict:
   ```python
   headers = {
       # … other headers …
       'cookie': 'PASTE_YOUR_FULL_COOKIE_VALUE_HERE',
       # …
   }


