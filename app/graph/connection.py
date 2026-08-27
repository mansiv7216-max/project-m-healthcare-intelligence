import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "projectm")

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

    def verify(self):
        self.driver.verify_connectivity()
        return True

    def close(self):
        self.driver.close()
