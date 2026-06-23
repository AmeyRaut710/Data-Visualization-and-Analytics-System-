import json
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class CleaningAgent:
    def __init__(self):
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.2,
                google_api_key=settings.GEMINI_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini for CleaningAgent: {e}")
            self.llm = None
            
    def recommend(self, issue: str, column: str, stats: dict) -> dict:
        if not self.llm:
            return {"recommended_method": "Keep As Is", "reason": "AI Engine Offline", "confidence": 0}
            
        prompt = f"""
        You are an expert Data Scientist. The user has requested a data cleaning recommendation.
        Issue: {issue}
        Affected Column(s): {column}
        Column Stats: {json.dumps(stats)}
        
        Provide your recommendation in the following JSON format strictly:
        {{
            "recommended_method": "Exact string matching one of the frontend methods",
            "reason": "A detailed explanation of why this is the best mathematical choice. For outliers, explicitly state the boundary condition violated (e.g. falls outside IQR range).",
            "confidence": 95
        }}
        
        Outlier Specific Rules:
        - If the outlier percentage is < 1%, ALWAYS recommend 'Manual Review'.
        - If the column represents business transactions (e.g. price, amount, salary, revenue), recommend 'Keep Outliers' as they might be rare genuine events.
        - If there are clear data-entry errors (e.g. values mathematically impossible or out of physical bounds), recommend 'Remove Outliers' or 'Replace with Median'.
        
        Duplicate Specific Rules:
        - Provide a brief Impact Analysis in your reason (e.g., "Duplicate transactions may inflate revenue").
        - For 'Exact Duplicates', recommend 'Remove Exact Duplicates' because there is no information loss.
        - For 'Business Duplicates', recommend 'Manual Review' because rows may contain additional information.
        
        Missing Values Specific Rules:
        - Provide a brief Impact Analysis in your reason (e.g., "Missing values in Customer Age may distort demographic analysis.").
        - If the column is Numeric and has outliers, recommend 'Median Imputation' (less affected by extreme values).
        - If the column is Numeric without outliers, recommend 'Mean Imputation' (maintains average distribution).
        - If the column is Categorical, recommend 'Mode Imputation' (preserves category distribution).
        - If the column is a Date field, recommend 'Forward Fill' (maintains chronological continuity).
        - If the Missing Percentage is > 50%, recommend 'Drop Column'.
        
        Frontend Methods Available based on Issue:
        If Issue == 'Missing Values': 'Mean Imputation', 'Median Imputation', 'Mode Imputation', 'Forward Fill', 'Backward Fill', 'Interpolate', 'Replace with Unknown', 'Drop Rows', 'Drop Column', 'Keep As Is'
        If Issue == 'Empty Cells': 'Remove Rows', 'Replace with Default Value', 'Replace with Mode', 'Replace with Custom User Value', 'Keep As Is'
        If Issue == 'Outliers': 'Remove Outliers', 'Cap to Upper Bound', 'Replace with Median', 'Replace with Mean', 'Keep Outliers', 'Manual Review'
        If Issue == 'Exact Duplicates': 'Remove Exact Duplicates', 'Keep First Occurrence', 'Keep Latest Occurrence', 'Manual Review'
        If Issue == 'Business Duplicates': 'Remove Exact Duplicates', 'Keep First Occurrence', 'Keep Latest Occurrence', 'Merge Records', 'Manual Review'
        If Issue == 'Near Duplicates': 'Merge Records', 'Manual Review', 'Keep First Occurrence'
        If Issue == 'Duplicate Columns': 'Drop Column', 'Keep As Is'
        If Issue == 'Constant Columns': 'Drop Column', 'Keep As Is'
        If Issue == 'High Cardinality': 'Drop Column', 'Keep As Is'
        If Issue == 'Extra Spaces': 'Trim Spaces', 'Keep As Is'
        If Issue == 'Special Characters': 'Remove Special Characters', 'Keep As Is'
        If Issue == 'Invalid Data Types': 'Convert to Numeric', 'Convert to String', 'Keep As Is'
        If Issue == 'Inconsistent Categories': 'Standardize Format', 'Keep As Is'
        If Issue == 'Date Format Problems': 'Convert to Single Format', 'Keep As Is'
        If Issue == 'High Null Percentage Columns': 'Drop Columns', 'Keep As Is'
        """
        
        try:
            res = self.llm.invoke(prompt)
            content = res.content
            # Clean markdown codeblocks
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"CleaningAgent recommendation failed: {e}")
            return {"recommended_method": "Keep As Is", "reason": f"Failed to generate recommendation: {str(e)}", "confidence": 0}
