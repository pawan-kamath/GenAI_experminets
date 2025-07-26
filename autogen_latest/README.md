## Search Agent Pre-reqs

Get the google custom search api key and app id

Go To: https://developers.google.com/custom-search/v1/overview and follow the prerequisites section



- **Get the search engine id:**
Go to https://programmablesearchengine.google.com/controlpanel/all and add a new search engine, and look for the **Search engine ID** on creation.
Save this ID in env variables as **GOOGLE_SEARCH_ENGINE_ID**.

- **Get the api key:**
    - Get the Custom Search API Key by clicking on **Get a Key** on https://developers.google.com/custom-search/v1/overview
    - Select/Create a project name
    - You are set! Get the key for that project, save that key in env variables as **GOOGLE_API_KEY**


**Note:** Custom Search JSON API provides 100 search queries per day for free. If you need more, you may sign up for billing in the API Console. Additional requests cost $5 per 1000 queries, up to 10k queries per day.
