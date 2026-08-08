import os
from typing import Dict, Any
from google.cloud import bigquery
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from agent_core.state import AgentState
from agent_core.validators.sql_parser import validate_sql_ast

# Initialize BigQuery & LLM
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "investment-treasury-ai")
bq_client = bigquery.Client(project=PROJECT_ID)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def schema_loader_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves relevant dbt mart schema metadata."""
    schema_info = """
    Dataset: dbt_dev_analytics
    Table: fct_liquidity_summary
    Columns:
      - asset_class (STRING): Classification (e.g., US_TREASURY, CORPORATE_BOND, EQUITY)
      - liquidity_tier (STRING): Risk tier (TIER_1_HIGH, TIER_2_MEDIUM, TIER_3_LOW)
      - total_trades (INTEGER): Count of trade executions
      - total_notional_exposure (NUMERIC): Aggregate monetary exposure
      - avg_yield_pct (NUMERIC): Average yield percentage
      - first_trade_at (TIMESTAMP)
      - last_trade_at (TIMESTAMP)
    """
    return {"schema_context": schema_info}

def sql_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generates BigQuery SQL from user query and schema context."""
    prompt = f"""
    You are an expert financial SQL engineer. Write a BigQuery SQL query to answer the question below.
    Return ONLY valid SQL inside a code block. Do not include markdown commentary outside the block.
    
    Schema:
    {state['schema_context']}
    
    Previous Error (if any):
    {state.get('validation_error', 'None')}
    
    Question:
    {state['question']}
    """
    response = llm.invoke(prompt)
    return {"generated_sql": response.content, "retry_count": state.get("retry_count", 0) + 1}

def ast_validator_node(state: AgentState) -> Dict[str, Any]:
    """Applies AST security and syntax validation."""
    is_valid, result = validate_sql_ast(state["generated_sql"])
    if is_valid:
        return {"is_valid_sql": True, "generated_sql": result, "validation_error": None}
    else:
        return {"is_valid_sql": False, "validation_error": result}

def bigquery_execution_node(state: AgentState) -> Dict[str, Any]:
    """Executes validated query safely against BigQuery."""
    try:
        query_job = bq_client.query(state["generated_sql"])
        results = [dict(row) for row in query_job.result()]
        return {"query_results": results}
    except Exception as e:
        return {"is_valid_sql": False, "validation_error": f"BigQuery Execution Error: {str(e)}"}

def response_synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes query results into executive financial insights."""
    prompt = f"""
    You are a Treasury Analyst. Provide a clear, executive-level summary answering the question based on these SQL query results.
    
    Question: {state['question']}
    SQL Executed: {state['generated_sql']}
    Data Results: {state['query_results']}
    """
    response = llm.invoke(prompt)
    return {"final_response": response.content}

# Routing Logic
def should_continue(state: AgentState) -> str:
    if state["is_valid_sql"]:
        return "execute_query"
    elif state["retry_count"] >= 3:
        return "failed_max_retries"
    else:
        return "retry_sql"

# Build LangGraph State Machine
workflow = StateGraph(AgentState)

workflow.add_node("load_schema", schema_loader_node)
workflow.add_node("generate_sql", sql_generator_node)
workflow.add_node("validate_ast", ast_validator_node)
workflow.add_node("execute_query", bigquery_execution_node)
workflow.add_node("synthesize_response", response_synthesis_node)

workflow.set_entry_point("load_schema")
workflow.add_edge("load_schema", "generate_sql")
workflow.add_edge("generate_sql", "validate_ast")

workflow.add_conditional_edges(
    "validate_ast",
    should_continue,
    {
        "execute_query": "execute_query",
        "retry_sql": "generate_sql",
        "failed_max_retries": END
    }
)

workflow.add_edge("execute_query", "synthesize_response")
workflow.add_edge("synthesize_response", END)

app = workflow.compile()
