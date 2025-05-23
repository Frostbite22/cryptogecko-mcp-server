import os
import json
import httpx
import argparse
from typing import Any, Dict, List, Optional

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from mcp.server import Server
from mcp.server.fastmcp import FastMCP
import mcp.types as types
from mcp.server.sse import SseServerTransport
from dotenv import load_dotenv


load_dotenv()

# CoinGecko API base URL
BASE_URL = "https://api.coingecko.com/api/v3"

# Create MCP server
mcp_app = FastMCP("crypto-mcp-server")
server = mcp_app._mcp_server

async def coin_price_request(vs_currencies: str, ids: str = None, symbols: str = None) -> Optional[Dict[str, Any]]:
    """
    Helper function to make CoinGecko API requests for coin prices
    """
    url = f"{BASE_URL}/simple/price"
    
    params = {
        "vs_currencies": vs_currencies,
    }
    
    if ids:
        params["ids"] = ids
    elif symbols:
        # Convert symbols to ids using coin list
        coin_list = await get_coin_list()
        if "error" in coin_list:
            return None
            
        symbol_to_id = {coin["symbol"]: coin["id"] for coin in coin_list}
        resolved_ids = []
        
        for symbol in symbols.split(","):
            if symbol in symbol_to_id:
                resolved_ids.append(symbol_to_id[symbol])
        
        if not resolved_ids:
            return {"error": "No valid symbols provided"}
            
        params["ids"] = ",".join(resolved_ids)
    
    headers = {
        "accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None


@mcp_app.tool()
async def get_coin_list() -> List[Dict[str, Any]] | Dict[str, str]:
    """Fetch list of available coins from CoinGecko"""
    url = f"{BASE_URL}/coins/list"
   
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": os.getenv("COINGECKO_API_KEY", ""),
    }
   
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"An error occurred: {e}")
            return {"error": f"Request error: {str(e)}"}
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return {"error": f"HTTP error: {str(e)}"}


@mcp_app.tool()
async def get_price(vs_currencies: str = "usd", ids: str = None, symbols: str = None) -> Dict[str, Any]:
    """
    Get the price of selected coins
   
    Args:
        vs_currencies: Comma-separated list of currencies (e.g., "usd,eur")
        ids: Comma-separated list of coin IDs (e.g., "bitcoin,ethereum")
        symbols: Comma-separated list of coin symbols (e.g., "btc,eth")
    """
    if not ids and not symbols:
        return {"error": "Please provide at least one coin id or symbol"}
   
    data = await coin_price_request(vs_currencies, ids, symbols)
    if data is not None:
        return data
    else:
        return {"error": "Failed to fetch price data"}

@mcp_app.tool()
async def get_market_data(
    vs_currency: str = "usd",
    ids: str = None,
    category: str = None,
    order: str = "market_cap_desc",
    per_page: int = 100,
    page: int = 1,
    sparkline: bool = False
) -> Dict[str, Any]:
    """
    Get cryptocurrency market data
    
    Args:
        vs_currency: The target currency (e.g., usd, eur)
        ids: Comma-separated list of coin IDs
        category: Filter by category
        order: Sort by field (market_cap_desc, volume_asc, etc.)
        per_page: Number of results per page
        page: Page number
        sparkline: Include sparkline data
    """
    url = f"{BASE_URL}/coins/markets"
    
    params = {
    "vs_currency": vs_currency,
    "order": order,
    "per_page": per_page,
    "page": page,
    "sparkline": str(sparkline).lower()
    }

    
    if ids:
        params["ids"] = ids
    
    if category:
        params["category"] = category
    
    headers = {
        "accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"An error occurred: {e}")
            return {"error": f"Request error: {str(e)}"}
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return {"error": f"HTTP error: {str(e)}"}


@mcp_app.tool()
async def get_trending() -> Dict[str, Any]:
    """Get trending coins in the last 24 hours"""
    url = f"{BASE_URL}/search/trending"
    
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": os.getenv("COINGECKO_API_KEY", ""),
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"An error occurred: {e}")
            return {"error": f"Request error: {str(e)}"}
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return {"error": f"HTTP error: {str(e)}"}

## We will start by get coin list and then get the trending coins prompts
PROMPTS = {
    "get_coin_list": types.Prompt(
        name="get_coin_list",
        description="Get a list of all coins available on CoinGecko",
    ),
    "get_price": types.Prompt(
        name="get_price",
        description="Get the price of selected coins",
        arguments=[
            types.PromptArgument(name="vs_currencies", description="Comma-separated list of currencies (e.g., 'usd,eur')", required=True),
            types.PromptArgument(name="ids", description="Comma-separated list of coin IDs (e.g., 'bitcoin,ethereum')",required=False),
            types.PromptArgument(name="symbols", description="Comma-separated list of coin symbols (e.g., 'btc,eth')", required=False),
        ],
    ),
    "get_market_data": types.Prompt(
        name="get_market_data",
        description="Get cryptocurrency market data",
        arguments=[
            types.PromptArgument(name="vs_currency", description="The target currency (e.g., 'usd', 'eur')", required=True),
            types.PromptArgument(name="ids", description="Comma-separated list of coin IDs", required=False),
            types.PromptArgument(name="category", description="Filter by category", required=False),
            types.PromptArgument(name="order", description="Sort by field (market_cap_desc, volume_asc, etc.)", required=False),
            types.PromptArgument(name="per_page", description="Number of results per page", required=False),
            types.PromptArgument(name="page", description="Page number", required=False),
            types.PromptArgument(name="sparkline", description="Include sparkline data", required=False),
        ],
    ),
    "get_trending": types.Prompt(
        name="get_trending",
        description="Get trending coins in the last 24 hours",
    ),
}

@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return list(PROMPTS.values())

@server.get_prompt()
async def get_prompt(
    name : str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    if name not in PROMPTS:
        raise ValueError(f"Prompt '{name}' not found.")
    
    if name == "get_coin_list":
        return types.GetPromptResult(
            messages = [
                types.PromptMessage(
                role="user",
                content = types.TextContent(
                    type="text",
                    text="Get a list of all coins available on CoinGecko",
                    ),
                ),
            ]      
        )
    
    if name == "get_price":
        
        vs_currencies = arguments.get("vs_currencies") if arguments.get("vs_currencies") else "usd"
        ids = arguments.get("ids") if arguments.get("ids") else ""
        symbols = arguments.get("symbols") if arguments.get("symbols") else ""
        
        text = f"Get the price of selected coins. vs_currencies: {vs_currencies}"
        if ids:
            text += f", ids: {ids}"
        if symbols:
            text += f", symbols: {symbols}"

        if not vs_currencies:
            raise ValueError("vs_currencies argument is required.")
        
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=text
                        )
                )
            ]
        )
    
    if name == "get_market_data":
        if arguments is None:
            raise ValueError("Arguments are required for this prompt.")
        
        vs_currency = arguments.get("vs_currency") if arguments.get("vs_currency") else "usd"
        ids = arguments.get("ids") if arguments.get("ids") else ""
        category = arguments.get("category") if arguments.get("category") else ""
        order = arguments.get("order") if arguments.get("order") else "market_cap_desc"
        per_page = arguments.get("per_page") if arguments.get("per_page") else 100
        page = arguments.get("page") if arguments.get("page") else 1
        sparkline = arguments.get("sparkline") if arguments.get("sparkline") else False
        
        text = f"Get cryptocurrency market data. vs_currency: {vs_currency}"
        if ids:
            text += f", ids: {ids}"
        if category:
            text += f", category: {category}"
        if order:
            text += f", order: {order}"
        if per_page:
            text += f", per_page: {per_page}"
        if page:
            text += f", page: {page}"
        if sparkline:
            text += f", sparkline: {sparkline}"

        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=text
                        )
                ),
            ]
        )
    
    if name == "get_trending":
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="Get trending coins in the last 24 hours"
                        )
                ),
            ]
        )
    
    raise ValueError("Prompt implementation not found")


# Health check endpoint
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "crypto-mcp-server"})

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided MCP server with SSE."""
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
    
    app = Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
            Route("/health", endpoint=health_check),
        ],
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Crypto MCP SSE-based server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.getenv("PORT", 8000)), help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Get the internal MCP server instance
    mcp_server = mcp_app._mcp_server
    
    # Create Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=args.debug)
    
    # Run the server
    import uvicorn
    print(f"Starting Crypto MCP server on {args.host}:{args.port}")
    uvicorn.run(starlette_app, host=args.host, port=args.port)
