Development Roadmap

### Phase 1: Local Development (No AWS needed yet)

Step 1: Simple standalone agent (simple_tutor.py)
- Single file, single agent
- Hardcode API design concepts
- Test the Strands Agent basics: prompts, tool calling, conversation loop
- Run locally, print to console

Step 2: Add the Tutor Agent (agents/tutor.py)
- Specialist agent focused on teaching
- Use @tool decorator for teaching functions
- Accept topic as parameter, explain with examples

Step 3: Add the Quiz Agent (agents/quiz.py)
- Another specialist agent
- Generates questions based on topic
- Evaluates free-form answers
- Returns scores and feedback

Step 4: Build the Orchestrator (agents/orchestrator.py)
- Parent agent that uses Agent-as-Tool pattern
- Registers tutor and quiz as tools using as_tool()
- Manages session flow: greet → teach → quiz → summarize

Step 5: Local test script (local_test.py)
- Import orchestrator
- Simulate conversation
- No state persistence yet, just prove the multi-agent pattern works

### Phase 2: Add State Persistence

Step 6: DynamoDB integration (tools/state.py)
- load_progress(user_id) - reads from DynamoDB
- save_progress(user_id, data) - writes scores, topics covered
- Orchestrator calls these before/after each session

Step 7: Test locally with DynamoDB
- Use DynamoDB Local or create a real table
- Verify state persists across sessions

### Phase 3: AWS Deployment

Step 8: Lambda handler (handler.py)
- Wraps orchestrator in Lambda function
- Accepts event from API Gateway
- Returns response

Step 9: SAM template (template.yaml)
- Define Lambda function
- Define DynamoDB table
- Define API Gateway endpoint
- Set IAM permissions for Bedrock + DynamoDB

Step 10: Deploy
- sam build
- sam deploy --guided
- Test via API Gateway URL

### Phase 4: Extensions (Optional)

- Conversation memory in DynamoDB
- Progress dashboard/report tool
- Adaptive difficulty based on scores
- OpenTelemetry + X-Ray tracing
- Migrate to BedrockAgentCore

## Recommended File Structure
```
  system-design-coach/
  ├── agents/
  │   ├── __init__.py
  │   ├── tutor.py          # Teaching specialist
  │   ├── quiz.py           # Quiz specialist
  │   └── orchestrator.py   # Parent coordinator
  ├── tools/
  │   ├── __init__.py
  │   └── state.py          # DynamoDB read/write
  ├── simple_tutor.py       # Start here - single file prototype
  ├── local_test.py         # Test orchestrator locally
  ├── handler.py            # Lambda entry point
  ├── template.yaml         # SAM deployment config
  ├── requirements.txt
  └── .env
```