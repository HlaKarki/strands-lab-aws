from agents.orcehstrator import create_orchestrator, save_session

orchestrator = create_orchestrator("test_user_12")

print("==== Starting Orchestrator ====")

orchestrator("Hi! I want to learn about API Design")

print("\n==== Asking Follow Up Question About Progress ====")
orchestrator("What's my current progress?")

print("\n==== Asking To Progress to Next Topic ====")
orchestrator("I can fully comprehend API Design concept now! What topic can i explore next?")

