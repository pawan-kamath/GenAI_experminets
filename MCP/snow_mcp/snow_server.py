import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# Authentication class for BasicAuth
class BasicAuth:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    async def get_headers(self) -> dict[str, str]:
        return {}

    def get_auth(self) -> tuple:
        return (self.username, self.password)


# Query options for listing knowledge articles
class QueryOptions(BaseModel):
    limit: int = Field(10, description="Maximum number of records", ge=1, le=100)
    offset: int = Field(0, description="Records to skip", ge=0)


# ServiceNow client for interacting with the API
class ServiceNowClient:
    def __init__(self, instance_url: str, auth: BasicAuth):
        self.instance_url = instance_url.rstrip("/")
        self.auth = auth
        self.client = httpx.AsyncClient(verify=False)

    async def close(self):
        await self.client.aclose()

    async def request(
        self, method: str, path: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        url = f"{self.instance_url}{path}"
        headers = {"Accept": "application/json"}
        auth_tuple = self.auth.get_auth()

        logger.info(f"Making request to {url} with params {params}")

        try:
            response = await self.client.request(
                method=method, url=url, params=params, headers=headers, auth=auth_tuple
            )
            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"ServiceNow API error: {e.response.text}")
            raise

    async def get_knowledge_article(self, sys_id: str, fields: str) -> dict[str, Any]:
        params = {"sysparm_fields": fields}
        return await self.request(
            "GET", f"/api/now/table/kb_knowledge/{sys_id}", params=params
        )

    async def list_knowledge_articles(self, params: dict[str, Any]) -> dict[str, Any]:
        return await self.request("GET", "/api/now/table/kb_knowledge", params=params)


# MCP server for ServiceNow knowledge articles
class ServiceNowKAMCP:
    def __init__(self, instance_url: str, username: str, password: str):
        auth = BasicAuth(username, password)
        self.client = ServiceNowClient(instance_url, auth)
        self.mcp = FastMCP("ServiceNow Knowledge Articles MCP")

        # Register tools
        self.mcp.tool(name="list_knowledge_articles")(self.list_knowledge_articles_tool)
        self.mcp.tool(name="get_knowledge_article")(self.get_knowledge_article_tool)
        self.mcp.tool(name="search_knowledge_articles")(
            self.search_knowledge_articles_tool
        )

        # Register new tools
        self.mcp.tool(name="count_articles_by_author")(
            self.count_articles_by_author_tool
        )
        self.mcp.tool(name="articles_by_state")(self.articles_by_state_tool)
        self.mcp.tool(name="articles_by_update_date")(self.articles_by_update_date_tool)

    async def close(self):
        await self.client.close()

    def run(self, transport: str = "stdio"):
        try:
            self.mcp.run(transport=transport)
        finally:
            asyncio.run(self.close())

    # Tool handlers
    async def list_knowledge_articles_tool(
        self, custom_kas: Optional[str] = None, author_email: Optional[str] = None
    ) -> str:
        logger.info(
            f"Tool 'list_knowledge_articles' invoked with custom_kas={custom_kas}, author_email={author_email}"
        )
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            previous_day = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            params = self.construct_query_parts(
                previous_day, today, custom_kas, author_email
            )
            result = await self.client.list_knowledge_articles(params)
            logger.info("Tool 'list_knowledge_articles' executed successfully.")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error in 'list_knowledge_articles_tool': {e}")
            raise

    async def get_knowledge_article_tool(self, article_number: str) -> str:
        logger.info(
            f"Tool 'get_knowledge_article' invoked with article_number={article_number}"
        )
        try:
            # Query by article number instead of sys_id
            params = {
                "sysparm_query": f"number={article_number}",
                "sysparm_fields": "sys_id,number,short_description,text,author,author.email,sys_updated_on,workflow_state,valid_to,valid_from,kb_knowledge_base",
                "sysparm_display_value": "all",
            }

            # Use the list endpoint to find the article by number
            result = await self.client.list_knowledge_articles(params)

            if result.get("result") and len(result["result"]) > 0:
                logger.info("Tool 'get_knowledge_article' executed successfully.")

                # Format the result to be more readable
                article = result["result"][0]
                formatted_result = {
                    "title": article.get("short_description", {}).get(
                        "display_value", "No title"
                    ),
                    "article_number": article.get("number", {}).get(
                        "display_value", "Unknown"
                    ),
                    "content": article.get("text", {}).get(
                        "display_value", "No content"
                    ),
                    "author": article.get("author", {}).get("display_value", "Unknown"),
                    "author_email": article.get("author.email", {}).get(
                        "display_value", "Unknown"
                    ),
                    "last_updated": article.get("sys_updated_on", {}).get(
                        "display_value", "Unknown"
                    ),
                    "state": article.get("workflow_state", {}).get(
                        "display_value", "Unknown"
                    ),
                    "valid_from": article.get("valid_from", {}).get(
                        "display_value", "Unknown"
                    ),
                    "valid_to": article.get("valid_to", {}).get(
                        "display_value", "Unknown"
                    ),
                }

                return json.dumps(formatted_result, indent=2)
            else:
                return json.dumps(
                    {"error": f"Knowledge article {article_number} not found"}, indent=2
                )
        except Exception as e:
            logger.error(f"Error in 'get_knowledge_article_tool': {e}")
            raise

    # Add these new tool handlers to the ServiceNowKAMCP class

    async def count_articles_by_author_tool(
        self, author_email: Optional[str] = None
    ) -> str:
        """Count knowledge articles by author email."""
        logger.info(
            f"Tool 'count_articles_by_author' invoked with author_email={author_email}"
        )
        try:
            if not author_email:
                return json.dumps({"error": "Author email is required"}, indent=2)

            params = {
                "sysparm_display_value": "all",
                "sysparm_fields": "number,short_description,author.email,workflow_state",
                "sysparm_query": f"author.email={author_email}",
            }

            result = await self.client.list_knowledge_articles(params)

            if result.get("result"):
                article_count = len(result["result"])

                # Count articles by state
                state_count = {}
                for article in result["result"]:
                    state = article.get("workflow_state", {}).get(
                        "display_value", "Unknown"
                    )
                    state_count[state] = state_count.get(state, 0) + 1

                response = {
                    "author_email": author_email,
                    "total_articles": article_count,
                    "articles_by_state": state_count,
                    "articles": [
                        {
                            "number": article.get("number", {}).get(
                                "display_value", "Unknown"
                            ),
                            "title": article.get("short_description", {}).get(
                                "display_value", "No title"
                            ),
                            "state": article.get("workflow_state", {}).get(
                                "display_value", "Unknown"
                            ),
                        }
                        for article in result["result"][
                            :10
                        ]  # Limit to first 10 for readability
                    ],
                }

                if article_count > 10:
                    response["note"] = f"Showing first 10 of {article_count} articles"

                return json.dumps(response, indent=2)
            else:
                return json.dumps(
                    {"error": f"No articles found for author {author_email}"}, indent=2
                )
        except Exception as e:
            logger.error(f"Error in 'count_articles_by_author_tool': {e}")
            raise

    async def articles_by_state_tool(self, state: str = "published") -> str:
        """Get knowledge articles filtered by workflow state."""
        logger.info(f"Tool 'articles_by_state' invoked with state={state}")
        try:
            params = {
                "sysparm_display_value": "all",
                "sysparm_fields": "sys_id,number,short_description,author,author.email,sys_updated_on,workflow_state",
                "sysparm_query": f"workflow_state={state}",
            }

            result = await self.client.list_knowledge_articles(params)

            if result.get("result"):
                article_count = len(result["result"])

                # Group by author
                authors = {}
                for article in result["result"]:
                    author_email = article.get("author.email", {}).get(
                        "display_value", "Unknown"
                    )
                    if author_email not in authors:
                        authors[author_email] = 0
                    authors[author_email] += 1

                response = {
                    "state": state,
                    "total_articles": article_count,
                    "articles_by_author": authors,
                    "articles": [
                        {
                            "number": article.get("number", {}).get(
                                "display_value", "Unknown"
                            ),
                            "title": article.get("short_description", {}).get(
                                "display_value", "No title"
                            ),
                            "author": article.get("author", {}).get(
                                "display_value", "Unknown"
                            ),
                            "author_email": article.get("author.email", {}).get(
                                "display_value", "Unknown"
                            ),
                            "last_updated": article.get("sys_updated_on", {}).get(
                                "display_value", "Unknown"
                            ),
                        }
                        for article in result["result"][
                            :10
                        ]  # Limit to first 10 for readability
                    ],
                }

                if article_count > 10:
                    response["note"] = f"Showing first 10 of {article_count} articles"

                return json.dumps(response, indent=2)
            else:
                return json.dumps(
                    {"error": f"No articles found with state '{state}'"}, indent=2
                )
        except Exception as e:
            logger.error(f"Error in 'articles_by_state_tool': {e}")
            raise

    async def articles_by_update_date_tool(self, date: str) -> str:
        """Get knowledge articles updated on a specific date (format: YYYY-MM-DD)."""
        logger.info(f"Tool 'articles_by_update_date' invoked with date={date}")
        try:
            # Validate date format
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                next_date = (parsed_date + timedelta(days=1)).strftime("%Y-%m-%d")
                date_str = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                return json.dumps(
                    {"error": "Invalid date format. Please use YYYY-MM-DD"}, indent=2
                )

            # Query for articles updated on the specific date
            params = {
                "sysparm_display_value": "all",
                "sysparm_fields": "sys_id,number,short_description,author,author.email,sys_updated_on,workflow_state",
                "sysparm_query": f"sys_updated_on>={date_str}^sys_updated_on<{next_date}",
            }

            result = await self.client.list_knowledge_articles(params)

            if result.get("result"):
                article_count = len(result["result"])

                response = {
                    "update_date": date,
                    "total_articles": article_count,
                    "articles": [
                        {
                            "number": article.get("number", {}).get(
                                "display_value", "Unknown"
                            ),
                            "title": article.get("short_description", {}).get(
                                "display_value", "No title"
                            ),
                            "author": article.get("author", {}).get(
                                "display_value", "Unknown"
                            ),
                            "author_email": article.get("author.email", {}).get(
                                "display_value", "Unknown"
                            ),
                            "state": article.get("workflow_state", {}).get(
                                "display_value", "Unknown"
                            ),
                            "last_updated": article.get("sys_updated_on", {}).get(
                                "display_value", "Unknown"
                            ),
                        }
                        for article in result["result"][
                            :10
                        ]  # Limit to first 10 for readability
                    ],
                }

                if article_count > 10:
                    response["note"] = f"Showing first 10 of {article_count} articles"

                return json.dumps(response, indent=2)
            else:
                return json.dumps(
                    {"error": f"No articles found updated on {date}"}, indent=2
                )
        except Exception as e:
            logger.error(f"Error in 'articles_by_update_date_tool': {e}")
            raise

    def construct_query_parts(
        self, today_str: str, custom_kas: Optional[str], author_email: Optional[str]
    ) -> dict[str, Any]:
        params = {
            "sysparm_display_value": "all",
            "sysparm_fields": "sys_id,number,short_description,author,author.email,sys_updated_on",
        }
        query_parts = ["workflow_state=Published", f"valid_to>{today_str}"]

        if custom_kas:
            # Handle multiple KA numbers correctly with proper OR syntax
            kas_list = [ka.strip() for ka in custom_kas.split(",") if ka.strip()]
            if kas_list:
                kas_query = "^ORnumber=" + "^ORnumber=".join(kas_list)
                # Replace the default query with specific article lookup
                query_parts = [kas_query]

        if author_email:
            query_parts.append(f"author.email={author_email}")

        params["sysparm_query"] = "^".join(query_parts)
        return params

    async def search_knowledge_articles_tool(
        self, query_text: str = None, article_number: str = None
    ) -> str:
        logger.info(
            f"Tool 'search_knowledge_articles' invoked with query={query_text}, article_number={article_number}"
        )
        try:
            params = {
                "sysparm_display_value": "all",
                "sysparm_fields": "sys_id,number,short_description,author,author.email,sys_updated_on",
            }

            query_parts = []

            if article_number:
                query_parts.append(f"number={article_number}")

            if query_text:
                # Search in short_description and text fields
                query_parts.append(
                    f"short_descriptionLIKE{query_text}^ORtextLIKE{query_text}"
                )

            if query_parts:
                params["sysparm_query"] = "^".join(query_parts)

            result = await self.client.list_knowledge_articles(params)
            logger.info("Tool 'search_knowledge_articles' executed successfully.")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error in 'search_knowledge_articles_tool': {e}")
            raise


# Main entry point
def main():
    # Load credentials from environment variables
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")

    if not instance_url or not username or not password:
        raise ValueError(
            "Missing required environment variables: SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, SERVICENOW_PASSWORD"
        )

    server = ServiceNowKAMCP(instance_url, username, password)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
