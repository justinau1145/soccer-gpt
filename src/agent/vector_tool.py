import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


class VectorTool:
    def __init__(self, vector_db_path: str = "data/vector_db", model_name: str = "all-MiniLM-L6-v2"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        
        self.vectorstore = Chroma(persist_directory=vector_db_path, 
                                  embedding_function=self.embeddings)
    
    def query(self, question: str, k: int = 3):
        """
        Query the vector database for relevant tactical knowledge.
        """
        try:
            results = self.vectorstore.similarity_search_with_score(question, k=k)
            
            if not results:
                return "No relevant tactical documents found."
            formatted_results = []
            for doc, score in results:
                source = doc.metadata.get('source', 'Unknown Manual')
                chunk_text = (
                    f"Source: {source}\n"
                    f"Content: {doc.page_content}\n"
                )
                formatted_results.append(chunk_text)
            
            return "\n".join(formatted_results)

        except Exception as e:
            return f"Vector search error: {str(e)}"


if __name__ == "__main__":
    tool = VectorTool()
    test_question = "How do goalkeepers distract penalty takers?"
    
    print(f"Question: {test_question}\n")
    answer = tool.query(test_question)
    print(answer)