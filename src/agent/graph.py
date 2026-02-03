import operator
from typing import Annotated, Sequence, TypedDict, Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from sql_tool import SQLTool
from vector_tool import VectorTool


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    route_to: str
    sql_context: str
    vector_context: str

llm = ChatOllama(model="llama3:latest", temperature=0)
sql_tool = SQLTool()
vector_tool = VectorTool()

def router_node(state: AgentState):
    question = state["messages"][-1].content
    
    prompt = ChatPromptTemplate.from_template("""
        You are a soccer query router. Categorize the user's question:
        - 'stats': numbers, scores, league tables, goal counts.
        - 'tactics': playstyles, manager philosophies, formations.
        - 'both': requires both statistical data and tactical context.
        
        Question: {question}
        Return JSON ONLY: {{"category": "stats/tactics/both"}}
    """)

    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"question": question})
    return {"route_to": result.get("category", "stats").lower()}

def route_after_router(state: AgentState):
    decision = state["route_to"]
    if decision == "tactics":
        return "tactics_retriever"
    return "stats_retriever"

def sql_node(state: AgentState):
    question = state["messages"][-1].content
    sql_result = sql_tool.query(question)
    return {"sql_context": sql_result}

def route_after_sql(state: AgentState):
    if state["route_to"] == "both":
        return "tactics_retriever"
    return "expert_synthesizer"

def vector_node(state: AgentState):
    question = state["messages"][-1].content

    search_query = question
    if state.get("sql_context"):
        search_query = f"{question} Context found: {state['sql_context']}"
    
    vector_result = vector_tool.query(search_query)
    return {"vector_context": vector_result}

def synthesizer_node(state: AgentState):
    prompt = f"""You are SoccerGPT, a world-class soccer analyst. 
    Use the retrieved contexts to provide a comprehensive answer.
    
    STATS DATA: {state.get('sql_context', 'No statistical data retrieved.')}
    TACTICAL DATA: {state.get('vector_context', 'No tactical data retrieved.')}
    
    USER QUESTION: {state['messages'][-1].content}
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router_node)
workflow.add_node("stats_retriever", sql_node)
workflow.add_node("tactics_retriever", vector_node)
workflow.add_node("expert_synthesizer", synthesizer_node)

# Set entry point
workflow.set_entry_point("router")

# Add conditional edges
workflow.add_conditional_edges(
    "router",
    route_after_router,
    {
        "stats_retriever": "stats_retriever",
        "tactics_retriever": "tactics_retriever"
    }
)

workflow.add_conditional_edges(
    "stats_retriever",
    route_after_sql,
    {
        "tactics_retriever": "tactics_retriever",
        "expert_synthesizer": "expert_synthesizer"
    }
)

workflow.add_edge("tactics_retriever", "expert_synthesizer")
workflow.add_edge("expert_synthesizer", END)

soccer_gpt = workflow.compile()

if __name__ == "__main__":
    question = "How do goalkeepers distract penalty takers?"
    response = soccer_gpt.invoke({
        "messages": [HumanMessage(content=question)]
    })
    print(response["messages"][-1].content)