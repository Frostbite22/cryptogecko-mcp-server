# MCP Crypto Client-Server Implementation Guide

This guide will help you set up the Model Context Protocol (MCP) server and client for retrieving cryptocurrency data using the CoinGecko API.

## Overview

The system consists of:
1. **Python MCP Server**: Handles API requests to CoinGecko and exposes functionality through MCP tools
2. **TypeScript MCP Client**: Connects to the server and provides methods to interact with the server tools
3. **React Frontend**: A web interface to interact with the crypto data

## Server Setup

### Prerequisites

- Python 3.9+
- pip

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install starlette uvicorn httpx mcp-server python-dotenv
   ```

3. Create a `.env` file in your project root:
   ```
   COINGECKO_API_KEY=your_api_key  # Optional, free tier can work without it
   PORT=8000
   ```

4. Save the Python server code to `server.py`

5. Start the server:
   ```bash
   python server.py --port 8000 --debug
   ```

   You can customize the host and port with command-line arguments:
   ```bash
   python server.py --host 127.0.0.1 --port 8080
   ```

The server will be available at `http://localhost:8000`.


## Customizing the Implementation

### Adding New Tools

To add a new tool to the server:

1. Create a new function with the `@mcp_app.tool()` decorator
2. Implement the function to fetch data from CoinGecko or process existing data
3. Add corresponding methods to the TypeScript client
4. Update the React UI to use the new functionality