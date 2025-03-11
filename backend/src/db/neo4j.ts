import neo4j from 'neo4j-driver';

const driver = neo4j.driver(
  process.env.NEO4J_URI || 'bolt://localhost:7687',
  neo4j.auth.basic(
    process.env.NEO4J_USER || 'neo4j',
    process.env.NEO4J_PASSWORD || 'password'
  )
);

const session = driver.session();

export async function getItems() {
  const result = await session.run('MATCH (i:Item) RETURN i');
  return result.records.map(record => ({
    id: record.get('i').properties.id,
    name: record.get('i').properties.name,
  }));
}

export async function addItem(name: string) {
  await session.run(
    'CREATE (i:Item {id: randomUUID(), name: $name}) RETURN i',
    { name }
  );
}

// Cleanup on app shutdown (optional, call in server.ts if needed)
export async function close() {
  await session.close();
  await driver.close();
}
