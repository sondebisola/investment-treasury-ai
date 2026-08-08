from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    question: str                  # User's natural language question
    schema_context: str            # Tables/columns retrieved from metadata
    generated_sql: Optional[str]   # Raw SQL produced by Gemini
    is_valid_sql: bool             # AST security & syntax validation status
    validation_error: Optional[str]# Error message if validation fails
    retry_count: int               # Self-correction loop safeguard
    query_results: Optional[List[Dict[str, Any]]] # Data returned from BigQuery
    final_response: Optional[str]  # Final human-readable response
