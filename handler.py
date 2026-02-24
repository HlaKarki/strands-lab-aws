import json
import os
from typing import Dict, Any
from agents.orcehstrator import create_orchestrator


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for API Gateway integration.
    Handles user requests and manages orchestrator sessions.

    Expected event body:
    {
        "user_id": "unique_user_identifier",
        "message": "User's message to the orchestrator"
    }

    :param event: API Gateway event
    :param context: Lambda context
    :return: API Gateway response
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        # Extract required fields
        user_id = body.get('user_id')
        message = body.get('message')

        # Validate input
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required field: user_id'
                })
            }

        if not message:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required field: message'
                })
            }

        # Create session-scoped orchestrator
        orchestrator = create_orchestrator(user_id)

        # Execute conversation turn
        response = orchestrator.execute(message)

        # Save session progress
        save_success = orchestrator.save()

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response,
                'progress_saved': save_success
            })
        }

    except Exception as e:
        # Log error
        print(f"Error in lambda_handler: {str(e)}")

        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def local_handler(user_id: str, message: str) -> str:
    """
    Local testing handler - simpler interface for development.

    :param user_id: Unique identifier for the user
    :param message: User's message
    :return: Orchestrator's response
    """
    orchestrator = create_orchestrator(user_id)
    response = orchestrator.execute(message)
    orchestrator.save()
    return response


if __name__ == "__main__":
    # Local testing
    print("==== Local Handler Test ====\n")

    test_user_id = "local_test_user"

    # Test conversation
    messages = [
        "Hi! What's my progress?",
        "Teach me about API Design & Microservices",
        "Quiz me on that topic"
    ]

    for msg in messages:
        print(f"User: {msg}")
        response = local_handler(test_user_id, msg)
        print(f"Bot: {response}\n")