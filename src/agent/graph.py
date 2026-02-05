import operator
from typing import Annotated, Sequence, TypedDict, Literal


from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


from src.agent.sql_tool import SQLTool
from src.agent.vector_tool import VectorTool
from src.agent.prompts import router_prompt, synthesizer_prompt




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
  
   prompt = ChatPromptTemplate.from_template(router_prompt)
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
   question = state["messages"][-1].content
   sql_context = state.get('sql_context', 'No statistical data retrieved.')
   vector_context = state.get('vector_context', 'No tactical data retrieved.')
  
   prompt = ChatPromptTemplate.from_template(synthesizer_prompt)
   chain = prompt | llm
   response = chain.invoke({"sql_context": sql_context,
                           "vector_context": vector_context,
                           "question": question})
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
   question = "Why does Arsenal win so many games?"
   response = soccer_gpt.invoke({
       "messages": [HumanMessage(content=question)]
   })
   print(response["messages"][-1].content)
