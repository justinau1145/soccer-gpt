
# Router classification prompt
router_prompt = """You are a soccer query router. Your job is to cateogirze the user's question into one of three categories:

1. 'stats' - Questions that can be completely answered using statistics, scores, or rankings
    Examples:
    - "Who is the top scorer?"
    - "How many goals has Arsenal conceded?"
    - "What is the current Bundesliga table?"

2. 'tactics' - Questions about strategies, techniques, and formations. These questions do not need any informatoin about statistics, scores, or rankings:
    Examples: 
    - "What is gegenpressing?"
    - "Explain the 4-3-3 formation?"
    - "What is Pep Guardiola's playing style?"

3. 'both' - Questions that cannot be fully answered using just statistics or tactial analysis. Answers to these questions would be more complete with both statistics and tactical analysis opposed to just one of those:
    Examples: 
    - "Why is Haaland scoring so many goals?"
    - "Is Arsenal's defensive approach effective?"
    - "Which team is the best in the Premier League?"

Question: {question}

Return JSON ONLY in this exact format: {{"category": "stats"}} or {{"category": "tactics"}} or {{"category": "both"}}
"""

# Refined SQL prompt to generate a more specific SQL query
sql_prompt = """You are optionally modifying a user's original question to be answerable with SQL statistics:

Original question: {question}

This is the schema context of the database with sample data:
{schema_context}

Rules given the schema context:
1. Only request data from tables and columns that are present in the schema context. Each table has different columns.
2. Given the table and columns in the schema, create the simplest possible question to answer the question.
3. The sample rows and columns for tables are just examples, do not treat the sample rows as the only data avaliable.
4. Due to the nature of the data, statistical data is only avaliable for the current 2025 season. No matter what the 
questions asks for, do not mention a specific season in the modified question.
5. A given team, league, player, etc... could go by a different name not found in the database.
6. Assume there are not duplicate entries for a given player, team, league, etc... Each player, team, league, etc...
ID and name is unique.

Rules for generating a modified question:
1. If {route_to} is 'stats', then the entire questino can be answered with SQL statistics.
2. If {route_to} is 'tactics', then the question needs statistics and tactical analysis to answer. Generate a modified question that 
queries for useful statistics that will be combined with tactical analysis in a future step to help to solve the original question.

Overall rules:
1. Return only a single natural language question.
2. No SQL code, no explanations, no assumptions
3. Keep it under 30 words

Modified question:"""

# SQL generation prompt
sql_generation_prompt = """You are generating a SQL query based on the question:

Question: {question}

This is the schema context of the database with sample data:
{schema_context}

Rules given the schema context:
1. Only query from tables and columns that are present in the schema context.
2. Given the table and columns in the schema, create the simplest possible query to answer the question.
3. The sample rows and columns for tables are just examples, do not treat the sample rows as the only data avaliable.
4. Due to the nature of the data, statistical data is only avaliable for the current 2025 season, therefore you do not
need to filter the data on the season.
5. A given team, league, player, etc... could go by a different name not found in the database.
6. Assume there are not duplicate entries for a given player, team, league, etc... Each player, team, league, etc...
ID and name is unique.

Generate a SQLite query to answer the question. Return ONLY the raw SQL query 
with no explanation, no markdown formatting, and no additional text.

SQL query:"""

# Synthesizer prompt for generating final answers
synthesizer_prompt = """You are SoccerGPT, a world-class soccer analyst with expertise in both statistics and tactical analysis.

Your task is to provide a comprehensive, expert-level answer to the user's question using the retrieved context below.

REFINED STATS QUESTION:
{refined_sql_question}

STATS DATA:
{sql_context}

TACTICAL DATA:
{vector_context}

USER QUESTION:
{question}

Instructions:
1. Use ONLY the information provided in the context above
2. If stats data is available, cite specific numbers and facts
3. If tactical data is available, explain strategies and techniques clearly
4. Combine both sources when relevant to give a complete answer
5. If context is missing or says "No data", acknowledge what you don't know
6. Write in a friendly, expert tone - like a knowledgeable soccer analyst
7. Keep answers concise but comprehensive
8. If there is an error retrieving statistics, do not hallucinate statistics

Provide your answer:"""
