import os
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import ChatOllama


class SQLTool:
    def __init__(self, db_path: str="data/soccer.db", model_name: str="llama3:latest"):
        self.engine = create_engine(f"sqlite:///{db_path}", 
                                  connect_args={"check_same_thread": False})
        self.db = SQLDatabase(self.engine)

        self.llm = ChatOllama(model=model_name, temperature=0)
        
        self.agent = create_sql_agent(llm=self.llm, db=self.db, agent_type="zero-shot-react-description", 
                                      verbose=True, handle_parsing_errors=True, max_iterations=5)
    
    def query(self, question: str) -> str:
        """
        Query the database with a natural language question.
        """
        try:
            response = self.agent.invoke({"input": question})
            return response.get("output", "No answer found.")
        except Exception as e:
            return f"Database error occurred: {str(e)}"


if __name__ == "__main__":
    tool = SQLTool()
    test_question = "Which team is currently top of the league?"
    
    print(f"Question: {test_question}\n")
    answer = tool.query(test_question)
    print(answer)