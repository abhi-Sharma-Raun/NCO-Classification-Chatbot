EXPANDER_OUTPUT_JSON_SCHEMA = {
    "name": "expander_output", # The function name the LLM sees
    "description": "Output the structured analysis of the user's job description.",
    "parameters": {
        "type": "object",
        "properties": {
            "reasoning": {
                "type": "string",
                "description": "Step-by-step analysis of user skills and tasks"
            },
            "division_reason": {
                "type": "string",
                "description": "Reason why it fits specific Division(s) or why it is ambiguous"
            },
            "title_reason": {
                "type": "string", # Explicitly allow null
                "description": "Why this title was chosen or why it is ambiguous. Return empty string if query is not generated."
            },
            "is_query_generated": {
                "type": "boolean",
                "description": "True if a search query was formed, False otherwise"
            },
            "query": {
                "type": "string",
                "description": "The structured semantic search string. Return empty string if input is too vague."
            },
            "note_for_analyzer": {
                "type": "string",
                "description": "CRITICAL: If the user's input was ambiguous and you had to make a assumption to pick a Division, explain it here.If there are other possible divisions explain that.",
            },
            "clarification_question": {
                "type": "string",
                "description": "Question to ask the user if no query could be formed.Return empty string if not needed."
            }
        },
        "required": ["reasoning", "division_reason", "is_query_generated", "note_for_analyzer"]
    }
}

ANALYZER_OUTPUT_JSON_SCHEMA = {
    "name": "analyzer_output",
    "description": "Output the final decision on the NCO occupation code.",
    "parameters": {
        "type": "object",
        "properties": {
            "thought_process": {
                "type": "string",
                "description": "Internal Phase 0-3 Audit."
            },
            "status": {
                "type": "string",
                "enum": ["MATCH_FOUND", "MORE_INFO", "IMPROVED_SEARCH"],
                "description": "The final status of the analysis."
            },
            "selected_code": {
                "type": "string",
                "description": "The selected NCO code (e.g., '1234.5600'). Empty string if no match."
            },
            "selected_title": {
                "type": "string",
                "description": "The official title corresponding to the selected code. Empty string if no match."
            },
            "confidence_score": {
                "type": "integer",
                "description": "Confidence score from 0-10."
            },
            "system_directive": {
                "type": "string",
                "description": "CRITICAL DYNAMIC FIELD. If status is 'IMPROVED_SEARCH', this MUST contain the new Search Query. If status is 'MATCH_FOUND' or 'MORE_INFO', this contains a short technical reasoning summary for the developer logs."
            },
            "user_message": {
                "type": "string",
                "description": "The final message to show the End User. If status is 'IMPROVED_SEARCH', return empty string \"\". If 'MATCH_FOUND', announce the result. If 'MORE_INFO', ask the clarification question."
            }
        },
        "required": ["thought_process", "status", "confidence_score", "system_directive", "user_message", "selected_code", "selected_title"]
    }
}

