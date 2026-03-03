import os
import re
from datetime import datetime
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from src.agent.prompts import prefix

load_dotenv()


class SQLTool:
    def __init__(self, db_path: str = "data/soccer.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", 
                                    connect_args={"check_same_thread": False}) 
        self.db = SQLDatabase(self.engine, sample_rows_in_table_info=0)                                  
        
        self.llm = ChatGroq(model=os.getenv("GROQ_API_MODEL1"), temperature=0,
                            api_key=os.getenv("GROQ_API_KEY"))
        
        self.schema_context = self._build_schema_context()

        self.agent = create_sql_agent(llm=self.llm, db=self.db, agent_type="zero-shot-react-description", 
                                      verbose=True, handle_parsing_errors=True, max_iterations=10,
                                      prefix=prefix)

    def _build_schema_context(self):
        """Build comprehensive schema context with tables, columns, and sample data."""
        tables = self.db.get_usable_table_names()
        schema_parts = ["DATABASE SCHEMA:\n"]

        for table in tables:
            table_info = self.db.get_table_info([table])
            schema_parts.append(f"\n{table_info}")

        return "\n".join(schema_parts)


    def query(self, question: str):
        """
        Query the database with a natural language question.
        """
        try:
            response = self.agent.invoke({"input": question})
            return response.get("output", "No answer found.")
        except Exception as e:
            return f"Error: {str(e)}"


if __name__ == "__main__":
    tool = SQLTool()
    test_question = "Which team is currently top of the premier league right now?"
    
    print(f"Question: {test_question}\n")
    answer = tool.query(test_question)
    print(answer)