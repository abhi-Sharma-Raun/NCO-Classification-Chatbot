from langchain_groq import ChatGroq
import chromadb
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from pathlib import Path
from .config import settings, EMBEDDINGS_PATH
import uuid
from typing import List, Optional
from .database import checkpointer_pool
from chromadb.utils import embedding_functions


llm=ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.01,
    max_retries=3,
    api_key=f"{settings.groq_api_key}"
)

client = chromadb.PersistentClient(EMBEDDINGS_PATH)
default_ef=embedding_functions.DefaultEmbeddingFunction()
collection=client.get_collection("EmbeddingsV-0.2_all-MiniLM-L6-v2", embedding_function=default_ef)


def parse_uuid(value: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(value)
    except:
        return None



def make_final_message(messages: List[BaseMessage]) -> str:

    final_message = ' '.join([msg.content for msg in messages if isinstance(msg, HumanMessage)])
    return final_message


def merge_retrieved_results(old: dict, new: dict):
    for key in ["distances", "documents", "metadatas", "ids"]:
        try:
            old[key][0].extend(new[key][0])
        except AttributeError:
            raise Exception("The retrieved_results do not have the necessary attributes")
        return old
   
def generate_initial_state(msg: str):
    initial_state_dict={
        "messages":[HumanMessage(content=msg)],
        "expander_analysis": None,
        "retrieved_results": None,
        "analyzer_response": None,
        "improved_search": False,
        "improved_search_count": 0   
    }
    return initial_state_dict
  

checkpointer = PostgresSaver(checkpointer_pool)