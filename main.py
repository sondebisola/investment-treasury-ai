import os
from agent_core.graph import app

if __name__ == "__main__":
    initial_state = {
        "question": "What is our total notional exposure and average yield broken down by asset class?",
        "retry_count": 0,
        "is_valid_sql": False
    }
    
    print("--- Starting Agentic SQL Pipeline Execution ---\n")
    final_state = app.invoke(initial_state)
    
    print("\n--- Executed Validated SQL ---")
    print(final_state.get("generated_sql"))
    
    print("\n--- Final Executive Summary ---")
    print(final_state.get("final_response"))
