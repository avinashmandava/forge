# Graph Extraction API

A FastAPI-based application that extracts entities and relationships from text and stores them in a Neo4j graph database.

## Project Structure

```
backend/
├── src/                  # Main application code
│   ├── api/              # API endpoints and routes
│   ├── models/           # Data models
│   ├── services/         # Business logic and services
│   ├── utils/            # Utility functions
│   └── app.py            # Main application entry point
├── tests/                # Test files
│   ├── testdata/         # Test input data
│   └── test_extraction.py # Test extraction functionality
├── scripts/              # Helper scripts
│   ├── run_api.py        # Script to run the API server
│   └── run_extraction_test.py # Script to run extraction tests
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in version control)
├── docker-compose.yml    # Docker Compose configuration
└── Dockerfile            # Docker configuration
```

## Setup and Installation

1. **Clone the repository**

2. **Set up environment variables**

   Create a `.env` file with:

   ```
   OPENAI_API_KEY=your_openai_api_key
   NEO4J_URI=bolt://neo4j:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   # Using Python directly
   python scripts/run_api.py

   # Using Docker
   docker-compose up -d
   ```

5. **Run tests**

   ```bash
   python scripts/run_extraction_test.py
   ```

## API Endpoints

- `POST /api/create_tenant` - Create a new tenant
- `POST /api/extract` - Extract data from text
- `POST /api/log` - Log extraction results
- `GET /` - Health check
