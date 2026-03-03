import os
import operator
from typing import Annotated, Sequence, TypedDict, Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import add_messages
from dotenv import load_dotenv

from src.agent.sql_tool import SQLTool
from src.agent.vector_tool import VectorTool
from src.agent.prompts import router_prompt, synthesizer_prompt, sql_prompt

load_dotenv()


class AgentState(TypedDict):
   messages: Annotated[Sequence[BaseMessage], add_messages]
   route_to: str
   sql_context: str
   vector_context: str
   refined_sql_question: str

routing_llm = ChatGroq(model=os.getenv("GROQ_API_MODEL2"), temperature=0,
                       api_key=os.getenv("GROQ_API_KEY"))
sql_llm = ChatGroq(model=os.getenv("GROQ_API_MODEL2"), temperature=0,
                   api_key=os.getenv("GROQ_API_KEY"))
synthesizer_llm = ChatGroq(model=os.getenv("GROQ_API_MODEL2"), temperature=0.5,
                           api_key=os.getenv("GROQ_API_KEY"))
sql_tool = SQLTool()
vector_tool = VectorTool()

def router_node(state: AgentState):
   question = state["messages"][-1].content
  
   prompt = ChatPromptTemplate.from_template(router_prompt)
   chain = prompt | routing_llm | JsonOutputParser()
   result = chain.invoke({"question": question})

   print(f"[DEBUG] Router result: {result}")
   return {"route_to": result.get("category", "stats").lower()}

def route_after_router(state: AgentState):
   decision = state["route_to"]
   if decision == "tactics":
       return "vector_node"
   return "sql_node"

def sql_node(state: AgentState):
   question = state["messages"][-1].content
   route_to = state["route_to"]
   
   prompt = ChatPromptTemplate.from_template(sql_prompt)
   chain = prompt | sql_llm
   response = chain.invoke({
       "question": question, 
       "route_to": route_to,
       "schema_context": sql_tool.schema_context
   })
   refined_sql_question = response.content
   
   print(f"[DEBUG] Refined SQL question: {refined_sql_question}")

   sql_result = sql_tool.query(refined_sql_question)

   print(f"[DEBUG] SQL result: {sql_result}\n")
   
   return {"sql_context": sql_result, "refined_sql_question": refined_sql_question}

def route_after_sql(state: AgentState):
   if state["route_to"] == "both":
       return "vector_node"
   return "synthesizer"

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
   refined_sql_question = state.get('refined_sql_question', 'NA')
  
   prompt = ChatPromptTemplate.from_template(synthesizer_prompt)
   chain = prompt | synthesizer_llm
   response = chain.invoke({"sql_context": sql_context,
                           "vector_context": vector_context,
                           "question": question,
                           "refined_sql_question": refined_sql_question})
   return {"messages": [response]}

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router_node", router_node)
workflow.add_node("sql_node", sql_node)
workflow.add_node("vector_node", vector_node)
workflow.add_node("synthesizer", synthesizer_node)

# Set entry point
workflow.set_entry_point("router_node")

# Add conditional edges
workflow.add_conditional_edges(
    "router_node",
    route_after_router,
    {
        "sql_node": "sql_node",
        "vector_node": "vector_node"
    }
)

workflow.add_conditional_edges(
    "sql_node",
    route_after_sql,
    {
        "vector_node": "vector_node",
        "synthesizer": "synthesizer"
    }
)

workflow.add_edge("vector_node", "synthesizer")
workflow.add_edge("synthesizer", END)

soccer_gpt = workflow.compile()


if __name__ == "__main__":
   question = "Who is the best player in the world?"
   response = soccer_gpt.invoke({
       "messages": [HumanMessage(content=question)]
   })
   print(response["messages"][-1].content)
