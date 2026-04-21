import httpx
import json

import main as api
from database import Queries, get_db
from fastapi import Depends
from sqlalchemy.orm import Session

class RAGChatbot:
    def __init__(self, db: Session):
        self.history = []   # Currently unused, as model would take too long
        self.query_manager = Queries(db=db)
        with open("chat_instructions.txt", 'r') as f:
            self.chat_instructions = f.read()
        with open("chat_data_selection.txt", 'r') as f:
            self.data_selection_instructions = f.read()

    def answer_query(self, query_text: str, db: Session = Depends(get_db)):
        model1_answer = self.select_source(query_text)["response"]
        print(f"{model1_answer=}")
        source = json.loads(model1_answer)
        print(f"{source=}")
        try:
            method = getattr(self.query_manager, source["method"])
            data = method()
            print(f"{data=}")
            #if len(data) < 20:
            data = data[source["index"]]
            knowledge = f"Result retrieved from source {source['method']}: {data}"
        except TypeError as e:  # Happens when method is null
            print("Case TypeError")
            return {"response": "The data selection model couldn't find a suitable data source for this query."}
        except Exception as e:
            print(f"Case Exception {e=}")
            return {"response": f"An error occurred with the answer of the source selection model: {type(e)}: {e}"}
        print(f"Asking model with knowledge: {data}")
        prompt = self.build_prompt(query_text, knowledge=knowledge, src=source["method"])
        answer = self.send_text(prompt)
        return answer

    def select_source(self, query_text: str):
        prompt = f"{self.data_selection_instructions}\n{query_text}"
        print("Selecting source with first prompt...")
        result = self.send_text(prompt)
        return result

    def build_prompt(self, query_text: str, knowledge: str, src: str):
        prompt = f"{self.chat_instructions}\n{knowledge}\nThis is the user query: {query_text}"
        return prompt

    def send_text(self, prompt: str):
        print(f"{prompt=}")
        try:
            response = httpx.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=400.0
            )
        except httpx.ReadTimeout:
            return {"response": "Request timed out, probably because generation took too long"}
        print(f"response={response.json()['response']}\n")
        return {"response": response.json()["response"]}