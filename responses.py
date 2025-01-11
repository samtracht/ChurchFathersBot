from random import choice, randint
from fathers.common.PineconeEngine import PineconeEngine
from fathers.common.MistralAIEngine import MistralAIEngine


def get_response(user_input: str) -> str:

    pinecone_engine = PineconeEngine("first-index", "first-namespace")
    mistral_engine = MistralAIEngine()

    embedding = mistral_engine.embed(user_input)[0]
    matches = pinecone_engine.query(embedding, k=5, filter=filter)

    return matches


def get_response_ai(user_input: str) -> str:

    pinecone_engine = PineconeEngine("first-index", "first-namespace")
    mistral_engine = MistralAIEngine()

    embedding = mistral_engine.embed(user_input)[0]
    matches = pinecone_engine.query(embedding, k=5, filter=filter)

    citations = "\n\n".join(
        [
            f"Citation: {i['metadata']['citation']}\n\n**Text**: {i['metadata']['text']}"
            for i in matches
        ]
    )
    output = mistral_engine.chat(question=user_input, citations=citations)

    return output
