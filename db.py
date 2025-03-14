async def cleanup_database():
    """Delete all nodes and relationships in the database."""
    with driver.session() as session:
        # Delete all relationships first
        session.run("MATCH ()-[r]->() DELETE r")
        # Then delete all nodes
        session.run("MATCH (n) DELETE n")
        return True
