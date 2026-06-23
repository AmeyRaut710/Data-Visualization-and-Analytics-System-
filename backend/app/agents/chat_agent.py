import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ChatAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.history = []

    def process_query(self, query: str) -> str:
        if not settings.GEMINI_API_KEY:
            return "Gemini API key is not configured. Please add it to your .env file."
        
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=settings.GEMINI_API_KEY, 
                temperature=0.2
            )
            
            prefix_prompt = """
            You are an expert Data Analyst AI. You are analyzing a pandas dataframe.
            You must understand the user's natural language question, even if it contains spelling mistakes or grammatical errors.
            Figure out the correct column names by looking at the dataframe columns.
            Write pandas code to answer the user's question, and return the final answer as a clear, concise English response.
            Do not just output the raw code. Output the actual answer to the question.
            """
            
            agent = create_pandas_dataframe_agent(
                llm,
                self.df,
                verbose=True,
                allow_dangerous_code=True,
                prefix=prefix_prompt
            )
            
            # Incorporate history into the query for context
            if self.history:
                history_str = "Recent Conversation History:\n" + "\n".join([f"User: {h['query']}\nAI: {h['response']}" for h in self.history[-3:]])
                full_query = f"{history_str}\n\nNow, answer the following New Question: {query}"
            else:
                full_query = query
            
            response = agent.invoke({"input": full_query})
            answer = response.get("output", "I could not analyze the data for that query.")
            
            self.history.append({"query": query, "response": answer})
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in Pandas agent: {str(e)}")
            return f"Error analyzing data: {str(e)}"

