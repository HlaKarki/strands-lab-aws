from agents.quiz import create_quiz_agent

quiz = create_quiz_agent()

# Test 1: Generate a question
print("==== Generating Question ====")
quiz("Generate a question about database sharding")

print("\n==== Generating Question ====")

# Test 2: Evaluate an Answer
question = "How would you design a rate limiter for an API?"
answer = """
I'd use a token bucket algorithm with Redis. Each user gets a bucket with tokens that
refill at a fixed rate. Each request consumes a token. If no tokens left, reject the request with 429.
"""

quiz(f"""
Evaluate this answer:
Question: {question}
Answer: {answer}
""")