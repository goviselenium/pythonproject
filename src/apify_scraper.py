import os
from typing import List, Dict, Any
from apify_client import ApifyClient
from src.config import APIFY_API_TOKEN, APIFY_ACTOR_ID

class ApifyJobScraper:
    def __init__(self, api_token: str = APIFY_API_TOKEN):
        self.api_token = api_token
        # Initialize client if token is provided, otherwise it will fail gracefully when called
        self.client = ApifyClient(api_token) if api_token else None

    def scrape_jobs(self, query: str, limit: int = 10, actor_id: str = APIFY_ACTOR_ID) -> List[Dict[str, Any]]:
        """
        Scrapes job listings from Google Jobs using Apify.
        Returns a list of dictionaries following the unified job schema.
        """
        if not self.api_token:
            raise ValueError(
                "Apify API token is not set. Please configure APIFY_API_TOKEN in your .env "
                "or provide it via the Streamlit dashboard."
            )
        
        # Determine actor and prepare input schema
        # Supported actors:
        # - johnvc/google-jobs-scraper
        # - apify/google-jobs-scraper
        # - veeronica/google-jobs-scraper
        
        run_input = {}
        if "google-jobs-scraper" in actor_id:
            # Most google jobs scrapers accept queries as an array or newline-separated string
            # and limit parameters like maxItems or maxPages
            run_input = {
                "queries": query,
                "maxItems": limit,
            }
            # Add specific variations if needed
            if actor_id == "johnvc/google-jobs-scraper":
                # johnvc scraper inputs
                run_input["maxPagesPerQuery"] = max(1, limit // 10)
        else:
            # Generic fallback
            run_input = {
                "queries": [query] if isinstance(query, str) else query,
                "maxItems": limit
            }

        print(f"Triggering Apify Actor '{actor_id}' with input: {run_input}")
        
        try:
            # Call the actor and wait for it to finish
            run = self.client.actor(actor_id).call(run_input=run_input)
        except Exception as e:
            error_str = str(e)
            # If the error suggests 'query' is required, retry with 'query' parameter
            if "query" in error_str.lower() or "input" in error_str.lower():
                print(f"First attempt failed: {e}. Retrying with 'query' instead of 'queries'...")
                fallback_input = {
                    "query": query,
                    "maxItems": limit
                }
                try:
                    run = self.client.actor(actor_id).call(run_input=fallback_input)
                except Exception as fallback_err:
                    print(f"Fallback attempt also failed: {fallback_err}")
                    raise fallback_err
            else:
                raise e
            
            # Retrieve items from the run's dataset
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                print("No dataset ID found in Apify run output.")
                return []
                
            items = list(self.client.dataset(dataset_id).iterate_items())
            print(f"Scraped {len(items)} raw listings from Apify.")
            
            # Map the raw items to our unified job schema
            return self._normalize_items(items)
            
        except Exception as e:
            print(f"Failed to scrape jobs from Apify: {e}")
            raise e

    def _normalize_items(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes various scraper output formats to a consistent internal representation:
        - title: str
        - company: str
        - location: str
        - description: str
        - url: str
        - posted_at: str
        """
        normalized = []
        for item in raw_items:
            # Resolve title
            title = item.get("title") or item.get("jobTitle") or item.get("job_title") or ""
            
            # Resolve company
            company = item.get("companyName") or item.get("company_name") or item.get("company") or ""
            
            # Resolve location
            location = item.get("location") or item.get("jobLocation") or "Remote"
            
            # Resolve description
            description = item.get("description") or item.get("jobDescription") or item.get("descriptionText") or ""
            
            # Resolve apply URL or job detail page URL
            url = item.get("applyUrl") or item.get("jobUrl") or item.get("url") or item.get("link") or ""
            
            # Resolve posted date
            posted_at = item.get("postedAt") or item.get("posted_date") or item.get("postedTime") or item.get("datePosted") or ""
            
            # Simple skip if minimal details are missing
            if not title or not company:
                continue
                
            normalized.append({
                "title": title.strip(),
                "company": company.strip(),
                "location": str(location).strip(),
                "description": description.strip(),
                "url": url.strip(),
                "posted_at": str(posted_at).strip()
            })
            
        return normalized
