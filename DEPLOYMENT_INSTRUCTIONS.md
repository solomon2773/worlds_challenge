# Deployment Instructions

## Quick Start

1. **Set up environment variables:**
   ```bash
   # Copy the environment template
   cp env.template .env
   
   # Edit with actual values
   nano .env
   ```

2. **Deploy with Docker Compose:**
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   - Open your browser to `http://localhost:5001`

## Environment Variables

The application requires these environment variables to be set:

**Required:**
- `GRAPHQL_TOKEN_ID` -  API token ID
- `GRAPHQL_TOKEN_VALUE` - API token value  
- `EVENT_PRODUCER_ID` - MUTATION: Event Producer ID
- `GRAPHQL_HTTP_ENDPOINT` - GraphQL http endpoint
- `GRAPHQL_WS_ENDPOINT` - GraphQL WebSocket Endpoint


**Optional:**
- `NAME_OF_THE_EVENT` - Custom event name 
These are automatically loaded from your `.env` file by docker-compose.yml.

