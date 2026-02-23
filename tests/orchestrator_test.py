from agents.orcehstrator import create_orchestrator

orchestrator = create_orchestrator()

print("==== Starting Orchestrator ====")

# Simulate a full session
messages = [
    "Hi, I want to prep for my system design interview. Start me on API design.",
    "Great! Teach me about REST vs gRPC.",
    # After explanation,
    "That makes sense. Now quiz me on API design.",
    # After getting quizzed
    "I would use REST with API Gateway, implement rate limiting with token bucket"
]

# Run first message
print(f"User: {messages[2]}")
response = orchestrator(messages[2])
