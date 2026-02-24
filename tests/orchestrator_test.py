from agents.orcehstrator import create_orchestrator

def test_orchestrator_session():
    """Test orchestrator with the new session-based pattern"""

    print("\n==== Starting Orchestrator Session ====\n")

    # Create orchestrator for a specific user
    orchestrator = create_orchestrator(user_id="test_user_123")

    # Test 1: Check user progress
    print("\nUser: What's my progress?")
    orchestrator.execute("What's my progress?")

    # Test 2: Request teaching
    print("\nUser: Teach me about API Design & Microservices")
    orchestrator.execute("Teach me about API Design & Microservices")

    # Test 3: Request quiz
    print("\nUser: Quiz me on API design")
    orchestrator.execute("Quiz me on API design")

    # Test 4: Answer a question (example)
    print("\nUser: I would use REST with API Gateway and implement rate limiting")
    orchestrator.execute("I would use REST with API Gateway and implement rate limiting")

    # Save progress at the end of session
    if orchestrator.save():
        print("\nSession progress saved successfully\n")
    else:
        print("\nFailed to save session progress\n")

    print("\n==== Session Ended ====")


if __name__ == "__main__":
    test_orchestrator_session()