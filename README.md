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

4. Save the Python server code to `improved_crypto_mcp_server.py`

5. Start the server:
   ```bash
   python improved_crypto_mcp_server.py --port 8000 --debug
   ```

   You can customize the host and port with command-line arguments:
   ```bash
   python improved_crypto_mcp_server.py --host 127.0.0.1 --port 8080
   ```

The server will be available at `http://localhost:8000`.

## Client Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Create a new React project:
   ```bash
   npx create-react-app crypto-mcp-client
   cd crypto-mcp-client
   ```

2. Install required dependencies:
   ```bash
   npm install @anthropic-ai/mcp-client tailwindcss
   ```

3. Set up Tailwind CSS:
   ```bash
   npx tailwindcss init
   ```

4. Update `tailwind.config.js`:
   ```javascript
   /** @type {import('tailwindcss').Config} */
   module.exports = {
     content: [
       "./src/**/*.{js,jsx,ts,tsx}",
     ],
     theme: {
       extend: {},
     },
     plugins: [],
   }
   ```

5. Add Tailwind directives to your CSS:
   ```css
   /* src/index.css */
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

6. Create TypeScript files:
   - Save the TypeScript client code to `src/CryptoMcpClient.ts`
   - Save the React component code to `src/CryptoDashboard.tsx`

7. Update `src/App.tsx` to use the dashboard:
   ```tsx
   import React from 'react';
   import './App.css';
   import CryptoDashboard from './CryptoDashboard';

   function App() {
     return (
       <div className="App">
         <CryptoDashboard />
       </div>
     );
   }

   export default App;
   ```

8. Start the client:
   ```bash
   npm start
   ```

The client will be available at `http://localhost:3000`.

## MCP Communication Flow

1. The client connects to the server using Server-Sent Events (SSE) at the `/sse` endpoint
2. The client creates a session with the server
3. The client calls MCP tools provided by the server
4. Communication between client and server happens through:
   - SSE connection for server-to-client messages
   - POST requests to `/messages/` for client-to-server messages
5. The server processes requests and returns results through the established SSE connection

## Available Tools

The server exposes four main tools:

1. **get_price**: Get cryptocurrency prices in various currencies
   - Parameters: `vs_currencies`, `ids`, `symbols`

2. **get_coin_list**: Get list of all available coins
   - No parameters required

3. **get_market_data**: Get detailed market data for cryptocurrencies
   - Parameters: `vs_currency`, `ids`, `category`, `order`, `per_page`, `page`, `sparkline`

4. **get_trending**: Get trending coins in the last 24 hours
   - No parameters required

## Customizing the Implementation

### Adding New Tools

To add a new tool to the server:

1. Create a new function with the `@mcp_app.tool()` decorator
2. Implement the function to fetch data from CoinGecko or process existing data
3. Add corresponding methods to the TypeScript client
4. Update the React UI to use the new functionality