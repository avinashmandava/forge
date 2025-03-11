Since we’re switching to Neo4j, the `README.md` needs an update to reflect the new database and setup instructions. Below is the revised README content, formatted in Markdown as output (not a file, per your preference). It’s tailored to the backend with Neo4j, keeping it concise and actionable.

---

# Forge Backend

This is the backend for Forge, built with Fastify, TypeScript, and Neo4j.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine.
- Basic familiarity with Node.js, TypeScript, and graph databases.

## Directory Structure

```
backend/
├── src/
│   ├── server.ts        # Fastify server setup
│   ├── routes/          # API routes
│   │   └── index.ts
│   ├── db/              # Database logic
│   │   └── neo4j.ts     # Neo4j connection and queries
│   └── types/           # TypeScript types
│       └── index.ts
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript config
├── Dockerfile           # Docker config for the backend
└── docker-compose.yml   # Local dev setup with Neo4j
```

## Getting Started

### 1. Clone the Repository

If this is part of a larger repo, navigate to the `backend/` directory:

```bash
cd backend
```

### 2. Start the Services

Run Docker Compose to build and start the backend and Neo4j:

```bash
docker-compose up --build
```

- This builds the backend image and starts:
  - **Fastify app**: `http://localhost:3000`
  - **Neo4j**: Port `7687` (Bolt protocol), `7474` (browser UI at `http://localhost:7474`)
- The app serves static files from `../frontend/public/` (create this directory with an `index.html` if testing).

### 3. Initialize the Database

No manual schema needed—Neo4j is schemaless. The API creates nodes (e.g., `Item`) on first use. Optionally, explore the graph:

```bash
# Open Neo4j browser UI at http://localhost:7474
# Login: neo4j/password
# Run: MATCH (n) RETURN n  (to see data after testing)
```

### 4. Test the Backend

- **API Endpoints**:
  - `GET /api/`: Fetch all items (Neo4j nodes).
  - `POST /api/add`: Add a new item (expects `{ "name": "string" }`, returns HTML `<li>` for HTMX).
- Example:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"name":"Test Item"}' http://localhost:3000/api/add
```

```bash
curl http://localhost:3000/api/
```

### 5. Stop the Services

Shut down the containers:

```bash
docker-compose down
```

- To reset the database, add `-v` to remove the data volume:

```bash
docker-compose down -v
```

## Development Notes

- **Hot Reloading**: The `src/` directory is mounted, so TypeScript changes reflect immediately (restart may be needed for some updates).
- **Environment Variables**: Configurable via `docker-compose.yml` (e.g., `NEO4J_PASSWORD`, `PORT`).
- **Graph Flexibility**: Neo4j supports dynamic workflows—add nodes/relationships as needed for CRM (e.g., `Contact`, `Deal`).

## Troubleshooting

- **Port Conflict**: If `3000`, `7474`, or `7687` is in use, edit `docker-compose.yml` (e.g., `3001:3000`).
- **Build Errors**: Ensure Docker has resources; rerun `docker-compose up --build`.
- **Neo4j Connection**: Verify `NEO4J_URI=bolt://neo4j:7687` matches the service name.

## Future Deployment

This setup is portable for cloud deployment (e.g., AWS, Fly.io). The `Dockerfile` and env vars keep it flexible—details TBD.
