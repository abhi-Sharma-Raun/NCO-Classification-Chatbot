from langgraph.graph import StateGraph
from langgraph.types import interrupt
from typing import TypedDict, List, Annotated, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.constants import END
from pydantic import Field
from .prompts import expander_prompt, analyzer_prompt
from . import schemas
from .. import utils
import uuid


llm_expander=utils.llm.with_structured_output(schemas.EXPANDER_OUTPUT_JSON_SCHEMA, method="json_mode")
llm_analyzer=utils.llm.with_structured_output(schemas.ANALYZER_OUTPUT_JSON_SCHEMA, method="json_mode")


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    expander_analysis: Annotated[Optional[dict], Field(description="This stores the analysis done by expander")]
    retrieved_results: Annotated[Optional[dict], Field(description="This stores the results retrieved after semantic search on the search_query sent by node1(expander_node)")]
    analyzer_response: Annotated[Optional[dict], Field(description="This stores the result of analysis done by the analyzer node")]
    improved_search: Annotated[bool, Field(description="This is an indicator for retrieval_node used to indicate whether the query has come from analyzer or not")]=False
    improved_search_count: Annotated[int, Field(description="This tells us if improved_search has been used before or not by Analyzer.")]=1
    
def expander_node(state: State):
    exp_system_prompt=expander_prompt.expander_system_message
    expander_msgs=[exp_system_prompt]+state['messages']
    expander_raw_response=llm_expander.invoke(expander_msgs)
    expander_response=schemas.ExpanderOutput.model_validate(expander_raw_response)
    return{                       # while return state modifications from this node
        "expander_analysis": expander_response,
        "retrieved_results": None,
        "analyzer_analysis": None,
        "improved_search": False,
        "improved_search_count": 1
    }
    
def retrieval_node(state: State):
    
    results=None
    search_query=None
    
    if state['improved_search']:
        search_query=state['analyzer_response'].system_directive
    elif state['expander_analysis'].is_query_generated:
        search_query=state['expander_analysis'].query
    elif not state['expander_analysis'].query and not state['expander_analysis'].is_query_generated:
        search_query=None
    else:
        raise ValueError(f"Inconsistent state: Value for is_query_generated is not algined with Value for search_query.")
        
    if search_query is not None:
        results=utils.collection.query(
            query_texts=[search_query],
            n_results=5
        )

    if state['improved_search']:
        results = utils.merge_retrieved_results(state['retrieved_results'], results)
    
    return {
        "retrieved_results": results,
        "improved_search": False
    }
    

def analyzer_node(state: State):
    analyzer_chat_prompt=analyzer_prompt.analyzer_chat_prompt

    user_input=[utils.message_formatter(x) for x in state['messages'] if isinstance(x,HumanMessage)]
    expander_reasoning=state['expander_analysis'].reasoning
    expander_division_reason=state['expander_analysis'].division_reason
    expander_title_reason=state['expander_analysis'].title_reason
    expander_query=state['expander_analysis'].query
    expander_note_for_analyzer=state['expander_analysis'].note_for_analyzer
    expander_clarification_question=state['expander_analysis'].clarification_question
    retrieved_results=state['retrieved_results']

    analyzer_formatted_messages=analyzer_chat_prompt.format_messages(
            user_input=user_input,
            expander_reasoning=expander_reasoning,
            expander_division_reason=expander_division_reason,
            expander_title_reason=expander_title_reason,
            expander_query=expander_query,
            expander_note_for_analyzer=expander_note_for_analyzer,
            expander_clarification_question=expander_clarification_question,
            retrieved_results=retrieved_results,
            improved_search_counter=state['improved_search_count']
    )
    
    improved_search=False
    count=state['improved_search_count']
    
    analyzer_raw_result=llm_analyzer.invoke(analyzer_formatted_messages)
    analyzer_result=schemas.AnalyzerOutput.model_validate(analyzer_raw_result)
    if analyzer_result.status=="IMPROVED_SEARCH":
        improved_search=True
        count=count-1       
        return {
        "analyzer_response": analyzer_result,
        "improved_search": improved_search,
        "improved_search_count": count            # It is decreased if improved_search 
        }
       
    return {
        "messages": [AIMessage(content=analyzer_result.user_message)],
        "analyzer_response": analyzer_result,
        "improved_search": improved_search,
        "improved_search_count": count
    }


def improved_search_router(state: State):
    if state['improved_search'] and state['improved_search_count']==0:
        return "retrieval_node"
    else:
        return "user_info_node"
    

def user_info_node(state: State) :
    current_status=state['analyzer_response'].status
    assert current_status!="IMPROVED_SEARCH", (
        "Improved_search must have resolved earlier."
    )
    if current_status=="MORE_INFO":
#        print("inside interrupt")
        clarification_response=interrupt(state['analyzer_response'].user_message)
#        print("going smooth")
        return {                          # In the return from this node only messages remain everything else needs to be cleared/reset
            "messages": [HumanMessage(content=clarification_response)],
            "expander_analysis": None,
            "retrieved_results": None,
            "analyzer_analysis": None,
            "improved_search": False,
            "improved_search_count": 0
            }
    else:           # When status == MATCH_FOUND
        return {}   
    
def user_info_router(state: State):

    if state['analyzer_response'].status == "MATCH_FOUND":
        return END
    else:   # when status == MORE_INFO.   IMPROVED_SEARCH will not reach here
        return "expander_node"
    

builder = StateGraph(State)
builder.add_node("expander_node", expander_node)
builder.add_node("analyzer_node", analyzer_node)
builder.add_node("retrieval_node", retrieval_node)
builder.add_node("user_info_node", user_info_node)
builder.add_edge("expander_node","retrieval_node")
builder.add_edge("retrieval_node","analyzer_node")
builder.add_conditional_edges("analyzer_node",improved_search_router, {"user_info_node": "user_info_node", "retrieval_node": "retrieval_node"})
builder.add_conditional_edges("user_info_node", user_info_router, {"expander_node": "expander_node", END: END})

builder.set_entry_point("expander_node")

config={"configurable": {"thread_id": uuid.uuid4()}}

graph = builder.compile(checkpointer=utils.checkpointer)


# Just for testing.You can use it to understand the behaviour if interrupt otherwise ignore
'''
user_input=input("Enter the job description: ")
initial_input_state={
    "messages": [HumanMessage(content=user_input)],
    "expander_analysis": None,
    "retrieved_results": None,
    "analyzer_response": None,
    "improved_search": False,
    "improved_search_count": 0
}

result=graph.invoke(initial_input_state, config=config)

while True:
    if "__interrupt__" in result:
        user_response=input(f"{result['__interrupt__'][0].value}:")
    
        result=graph.invoke(Command(resume=user_response), config=config)
        break
    else:
        pass
        
print("Ok till now")
print("/n")
print(result)

# print("Detailed Analyzer Response:")
# print(json.dumps(result['analyzer_response'], indent=4))
'''