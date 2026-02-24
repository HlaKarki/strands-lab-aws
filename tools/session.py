from typing import Optional, Dict, Any
from dataclasses import dataclass
from tools.state import load_progress, save_progress, update_topic_progress

ALL_TOPICS = [
    "API Design & Microservices",
    "Scalability & Distributed Systems",
    "Database Design & Data Modeling",
    "Cloud-Native & AWS Architecture"
]

@dataclass
class SessionContext:
    """
    Encapsulates session state - replaces global variables with a proper class.
    Thread-safe and supports concurrent user sessions.
    """
    user_id: str
    progress: Dict[str, Any]

    @classmethod
    def create(cls, user_id: str) -> "SessionContext":
        """
        Factory method: creates session and loads progress from DynamoDB.

        :param user_id: Unique identifier for the user
        :return: SessionContext instance with loaded progress
        """
        progress = load_progress(user_id)
        topics_count = len(progress.get('topics_covered', []))
        print(f"📊 Session created for {user_id}: {topics_count} topics completed")
        return cls(user_id=user_id, progress=progress)

    def update_topic(self, topic: str, quiz_score: Optional[float] = None) -> bool:
        """
        Update progress for a specific topic.

        :param topic: Topic name (e.g., 'API Design & Microservices')
        :param quiz_score: Optional quiz score (0-100)
        :return: True if update was successful
        """
        success = update_topic_progress(self.user_id, topic, quiz_score)
        if success:
            # Refresh progress from DynamoDB
            self.progress = load_progress(self.user_id)
        return success

    def save(self) -> bool:
        """
        Persist current session state to DynamoDB.

        :return: True if save was successful
        """
        return save_progress(self.user_id, self.progress)

    def get_summary(self) -> str:
        """
        Get a formatted progress summary for display to the user.

        :return: Formatted string with topics covered, scores, and suggestions
        """
        topics = self.progress.get('topics_covered', [])
        scores = self.progress.get('quiz_scores', {})

        summary = f" Topics covered: {len(topics)}/{len(ALL_TOPICS)}\n"

        if topics:
            summary += "\n Completed:\n"
            for topic in topics:
                score = scores.get(topic, "Not quizzed")
                summary += f"  • {topic}: {score}\n"

        # Suggest next uncovered topic
        uncovered = [t for t in ALL_TOPICS if t not in topics]
        if uncovered:
            summary += f"\n Next suggested: {uncovered[0]}"
        else:
            summary += "\n All topics completed!"

        return summary
