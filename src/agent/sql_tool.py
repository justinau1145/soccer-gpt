import os
import re
from datetime import datetime
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


class SQLTool:
    def __init__(self, db_path: str = "data/soccer.db"):
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
        self.db = SQLDatabase(self.engine)
        self.llm = ChatGroq(model=os.getenv("GROQ_API_MODEL"), temperature=0,
                            api_key=os.getenv("GROQ_API_KEY"))
        self.schema_context = self._build_schema_context()
        self.sql_query = ""

    def _build_schema_context(self) -> str:
        """Build comprehensive schema context with tables, columns, and sample data."""
        tables = self.db.get_usable_table_names()
        schema_parts = ["DATABASE SCHEMA:\n"]

        for table in tables:
            table_info = self.db.get_table_info([table])
            schema_parts.append(f"\n{table_info}")

        return "\n".join(schema_parts)

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Strip markdown code fences from a string."""
        return re.sub(r'```(?:sql)?\s*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL).strip()

    @staticmethod
    def _is_safe_query(sql: str) -> bool:
        """Only allow SELECT statements to prevent destructive operations."""
        return sql.strip().upper().startswith("SELECT")

    def query(self, question: str) -> str:
        """
        Query the database with a natural language question.
        """
        try:
            from prompts import sql_generation_prompt
            
            prompt = sql_generation_prompt.format(
                schema_context=self.schema_context,
                question=question
            )

            response = self.llm.invoke(prompt)
            self.sql_query = self._strip_markdown(response.content)
            
            if not self._is_safe_query(self.sql_query):
                return "Error: Only SELECT queries are permitted."

            result = self.db.run(self.sql_query)

            if result:
                cleaned = str(result).strip("[]()").replace("'", "").replace('"', '').replace(',', '')
                return cleaned.strip()
            else:
                return "No data found."

        except Exception as e:
            return f"Database error occurred: {str(e)}"


if __name__ == "__main__":
    tool = SQLTool()
    test_question = "Which team has the most goals scored in the Bundesliga"

    print(f"Question: {test_question}\n")
    answer = tool.query(test_question)
    print(f"Schema context: {tool.schema_context}\n")
    print(f"SQL Query: {tool.sql_query}\n")
    print(answer)