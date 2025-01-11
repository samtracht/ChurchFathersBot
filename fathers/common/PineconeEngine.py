from pinecone import ServerlessSpec
from pinecone.grpc import PineconeGRPC as Pinecone

from dotenv import load_dotenv
import os

load_dotenv()


class PineconeEngine:

    def __init__(self, index_name: str, namespace: str):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.create_index(index_name)
        self.index = self.pc.Index(index_name)
        self.namespace = namespace

    def get_count(self):
        self.index.count()

    def create_index(self, index_name: str):
        if self.pc.has_index(index_name):
            print(f"Index has already been created for {index_name}")
            return

        self.pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    def upsert_records(self, data: list[dict]):
        for i in range(0, len(data), 50):
            self.index.upsert(vectors=data[i : i + 50], namespace=self.namespace)

    def query(
        self,
        vector: str,
        k: int = 5,
        filter: dict = {},
    ):
        results = self.index.query(
            namespace=self.namespace,
            vector=vector,
            top_k=k,
            include_values=False,
            include_metadata=True,
        )
        return results["matches"]
