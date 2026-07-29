import logging


logger = logging.getLogger(__name__)


class QuizWorker:
    """
    Worker for generating quizzes from transcript.
    """

    def process(
        self,
        transcript: str,
    ) -> list[dict]:

        logger.info(
            "Generating quiz.",
        )

        # TODO:
        # Replace with LLM generation later

        quizzes = [
            {
                "type": "multiple_choice",
                "question": "What is the main topic?",
                "answer": "AI",
                "options": "AI,ML,Database,Network",
            }
        ]

        logger.info(
            "Quiz generated.",
        )

        return quizzes