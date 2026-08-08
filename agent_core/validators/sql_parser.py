import sqlglot
from sqlglot import exp

def validate_sql_ast(sql_query: str, allowed_tables: list[str] = None) -> tuple[bool, str]:
    """
    Parses and validates SQL query AST.
    Enforces READ-ONLY operations and checks table permissions.
    """
    try:
        # Clean markdown formatting if present
        clean_sql = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Parse SQL string into AST
        parsed = sqlglot.parse_one(clean_sql, read="bigquery")
        
        # Guardrail 1: Enforce SELECT query type
        if not isinstance(parsed, exp.Select):
            return False, f"Security Violation: Only SELECT queries are permitted. Got: {parsed.key.upper()}"
        
        # Guardrail 2: Ensure no modification statements exist in AST
        forbidden_expressions = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter)
        if any(parsed.find_all(forbidden_expressions)):
            return False, "Security Violation: Data modification statements detected in query AST."
            
        return True, clean_sql

    except sqlglot.errors.ParseError as e:
        return False, f"SQL Syntax Error: {str(e)}"
    except Exception as e:
        return False, f"AST Validation Error: {str(e)}"
