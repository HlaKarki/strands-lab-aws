import datetime
import os
from typing import Any, Optional, Dict

import boto3

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

TABLE_NAME = "SystemDesignProgress"

def get_table():
    """Get DynamoDB table reference"""
    return dynamodb.Table(TABLE_NAME)

def load_progress(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load user progress from DynamoDB

    :param user_id: Unique identifier for the user
    :return: Dictionary containing user progress or None if not found
    Expected structure:
    {
        "user_id": str,
        "topics_covered": list,
        "quiz_scores": dict,
        "current_topic": str,
        "last_updated": str,
        "session_count": int
    }
    """
    try:
        table = get_table()
        response = table.get_item(Key={"user_id": user_id})

        if "Item" in response:
            return response["Item"]
        else:
            # Return default structure
            return {
                "user_id": user_id,
                "topics_covered": [],
                "quiz_scores": {},
                "current_topic": None,
                "last_updated": datetime.datetime.now(datetime.UTC),
                "session_count": 0
            }
    except Exception as e:
        print(f"Error loading progress for user {user_id}: {str(e)}")
        return {
            "user_id": user_id,
            "topics_covered": [],
            "quiz_scores": {},
            "current_topic": None,
            "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
            "session_count": 0
        }

def save_progress(user_id: str, data: Dict[str, Any]) -> bool:
    """
    Save user progress to DynamoDB

    :param user_id: Unique identifier for the user
    :param data: Dictionary containing user progress

    :return: True if save was successful, False otherwise
    """
    try:
        table = get_table()

        data["user_id"] = user_id
        data["last_updated"] = datetime.datetime.now(datetime.UTC).isoformat()

        if 'session_count' not in data:
            current = load_progress(user_id)
            data["session_count"] = current.get('session_count', 0) + 1

        table.put_item(Item=data)
        return True

    except Exception as e:
        print(f"Error saving progress for user {user_id}: {str(e)}")
        return False

def update_topic_progress(user_id: str, topic: str, quiz_score: Optional[float] = None) -> bool:
    """
    Update progress for a specific topic

    :param user_id: Unique identifier for the user
    :param topic: Topic name
    :param quiz_score: Optional quiz score for the topic
    :return: True if update was successful, False otherwise
    """
    try:
        progress = load_progress(user_id)

        if topic not in progress['topics_covered']:
            progress['topics_covered'].append(topic)

        if quiz_score is not None:
            progress['quiz_scores'][topic] = quiz_score

        progress['current_topic'] = topic

        return save_progress(user_id, progress)
    except Exception as e:
        print(f"Error updating topic progress for user {user_id}: {str(e)}")
        return False

def get_next_topic(user_id: str, all_topics: list) -> Optional[str]:
    """
    Get the next topic that hasn't been covered yet

    :param user_id: Unique identifier for the user
    :param all_topics: List of all available topics
    :return: Next uncovered topic or None if not found
    """
    progress = load_progress(user_id)
    covered = set(progress['topics_covered'])

    for topic in all_topics:
        if topic not in covered:
            return topic

    return None

