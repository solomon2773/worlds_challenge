# Deployment Instructions

## System Requirements
- OS: Linux, macOS, or Windows (with WSL2)
- Docker Engine >= 20.10
- Docker Compose (v2) or the `docker compose` CLI
- Git


## Quick Start

1. Clone the repository and set up environment variables:
   ```bash
   git clone https://github.com/solomon2773/worlds_challenge.git
   cd worlds_challenge
   
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
   - default login username : WorldsIO
   - default login password : LetMe!n@2025!!!

## Environment Variables

The application requires these environment variables to be set:

**Required:**
- `GRAPHQL_TOKEN_ID` -  API token ID
- `GRAPHQL_TOKEN_VALUE` - API token value  
- `EVENT_PRODUCER_ID` - MUTATION: Event Producer ID
- `GRAPHQL_HTTP_ENDPOINT` - GraphQL https endpoint
- `GRAPHQL_WS_ENDPOINT` - GraphQL WebSocket Endpoint


**Optional:**
- `NAME_OF_THE_EVENT` - Custom event name 
These are automatically loaded from your `.env` file by docker-compose.yml.

