from agents.tutor import create_tutor_agent

tutor = create_tutor_agent()

# Test teaching API Design
response = tutor("Teach me about REST vs gRPC. When should I use each?")
print(response)

"""
Success criteria:

  Run it and see if the agent:
  - Explains REST vs gRPC clearly
  - Mentions trade-offs (REST for public APIs, gRPC for internal/performance)
  - Gives AWS examples (API Gateway for REST, gRPC on ECS/EKS)
  - Sounds like a helpful tutor, not just documentation
"""
