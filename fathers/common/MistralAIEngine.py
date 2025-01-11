from mistralai import Mistral
from typing import Union
from dotenv import load_dotenv
import os
import time

load_dotenv()


class MistralAIEngine:

    SYS_PROMPT = """
    You are an Eastern Orthodox theologian who is trying to answer the questions of a student of yours.
    They ask you a question which will be listed below preceding 'question:'. 
    You will also be given a certain number of texts and citations that are relevant to the question.
    Using the cited texts alone try and answer the students question.
    If you cannot answer the question please say so.
    Make reference to the citation exactly as I have given it to you if it is in fact used.
    Return the ouput in Markdown format.
    Any lists make them as regular bullets and not numbered.
    Be very detailed and organized. 
    Make this look scholarly and formatted extremely well with good citations.
    Make reference to as many of the citations as possible.
    List all the citations at the bottom of the result as well.
    Make sure that all responses are less than 4000 characters.
    """

    USER_PROMPT = """
    Question: {question}\n
    Text and Citations:{citations}
    """

    def __init__(
        self,
        chat_model: str = "mistral-large-latest",
        embed_model: str = "mistral-embed",
    ):

        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.chat_model = chat_model
        self.embed_model = embed_model

    def embed(self, data: Union[list[str], str]) -> list[list[float]]:

        for i in range(5):
            try:
                results = self.client.embeddings.create(
                    model=self.embed_model, inputs=data
                )
                return [result.embedding for result in results.data]

            except Exception as e:
                if len(e.args) > 1 and e.args[1] == 400:
                    return
                elif len(e.args) > 1 and e.args[1] == 429:
                    print(
                        f"429 Error on try {i} -- Sleeping... will retry in 2 seconds"
                    )
                    time.sleep(2)
                else:
                    print(e)

        raise Exception("Could not complete embedding")

    def chat(self, question: str, citations: str):

        results = self.client.chat.complete(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": MistralAIEngine.SYS_PROMPT},
                {
                    "role": "user",
                    "content": MistralAIEngine.USER_PROMPT.format(
                        question=question, citations=citations
                    ),
                },
            ],
        )
        return results.choices[0].message.content
