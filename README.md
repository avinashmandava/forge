# AI-Native CRM Platform

An intelligent CRM system that leverages AI for automatic data capture, conversational interactions, and proactive insights.

## Features

- 🤖 Automatic data extraction from conversations
- 💬 Natural language interface for CRM operations
- 📊 AI-powered deal insights and recommendations
- 🔄 Adaptive workflow management
- 📈 Proactive pipeline monitoring

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-crm
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
- Copy `.env.example` to `.env`
- Fill in your API keys and configuration

5. Set up the database:
```bash
# Install PostgreSQL if not already installed
# Create a new database named 'crm_db'
createdb crm_db
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key Endpoints

- `POST /process-interaction/`: Process natural language interactions
- `POST /companies/`: Create a new company
- `POST /contacts/`: Create a new contact
- `POST /deals/`: Create a new deal
- `GET /companies/`: List all companies
- `GET /contacts/`: List all contacts
- `GET /deals/`: List all deals

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `PINECONE_API_KEY`: Pinecone API key for vector storage
- `ENVIRONMENT`: Development/production environment

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Format code:
```bash
black .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT
