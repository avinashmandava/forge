# Forge

A powerful data extraction and processing system.

## Development Setup

You can run this project either locally for faster development cycles or using Docker for a more isolated environment.

### Local Development Setup

1. **Prerequisites**
   - Python 3.11+ (recommended to use pyenv)
   - Neo4j installed locally (`brew install neo4j` on macOS)
   - Python virtual environment (e.g., `pyenv virtualenv 3.11.11 forge`)

2. **Environment Setup**
   ```bash
   # Activate your virtual environment
   pyenv activate forge

   # Install dependencies
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Neo4j**
   ```bash
   # Start Neo4j service
   brew services start neo4j

   # Set initial password (first time only)
   # Visit http://localhost:7474 and set password to match your .env file
   # Default username: neo4j
   # Set password to: password (or update .env accordingly)
   ```

4. **Environment Variables**
   ```bash
   # Ensure your backend/.env file exists with:
   OPENAI_API_KEY=your_api_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ```

5. **Run the Application**
   ```bash
   # Load environment variables and start the server with hot-reload
   uvicorn app:app --reload --port 8000 --env-file .env
   ```

   The API will be available at http://localhost:8000

### Docker Development Setup

1. **Prerequisites**
   - Docker and Docker Compose installed

2. **Environment Setup**
   ```bash
   # Ensure your backend/.env file exists with proper configuration
   # The Neo4j URI should point to the Docker service:
   OPENAI_API_KEY=your_api_key
   NEO4J_URI=bolt://neo4j:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ```

3. **Run with Docker Compose**
   ```bash
   cd backend
   docker-compose up --build
   ```

   The API will be available at http://localhost:8000

## API Testing

Test the API is working by creating a tenant:
```bash
curl -X POST http://localhost:8000/api/create_tenant \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Test Tenant"}'
```

## Development Notes

- Local development provides faster feedback cycles with hot-reload
- Docker setup provides a consistent environment across different machines
- Both setups use the same environment variables and configurations
- Neo4j browser interface is available at http://localhost:7474

