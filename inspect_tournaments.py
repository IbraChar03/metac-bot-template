"""
Print the open and upcoming questions of the tournaments the bot targets, with
their open and close times. Read-only: no forecasts and no LLM calls.
"""

import asyncio

import dotenv

from forecasting_tools import ApiFilter, MetaculusClient

dotenv.load_dotenv()

TOURNAMENTS = {
    "minibench": "minibench",
    "fall-futureeval-2026": 33121,
    "metaculus-cup-fall-2026": 33108,
}
SHOWN_PER_STATUS = 12


async def main() -> None:
    client = MetaculusClient()
    for name, tournament_id in TOURNAMENTS.items():
        for status in ("open", "upcoming"):
            api_filter = ApiFilter(
                allowed_tournaments=[tournament_id],
                allowed_statuses=[status],
                group_question_mode="unpack_subquestions",
            )
            try:
                questions = await client.get_questions_matching_filter(
                    api_filter, error_if_question_target_missed=False
                )
            except Exception as error:  # noqa: BLE001
                print(f"{name} [{status}]: error {type(error).__name__}: {error}")
                continue
            questions.sort(key=lambda q: (q.open_time is None, q.open_time))
            print(f"\n{name} [{status}]: {len(questions)} questions")
            for question in questions[:SHOWN_PER_STATUS]:
                print(
                    f"  opens {question.open_time:%Y-%m-%d %H:%M} | "
                    f"closes {question.close_time:%Y-%m-%d %H:%M} | "
                    f"{type(question).__name__:<22} | {question.question_text[:70]}"
                    if question.open_time and question.close_time
                    else f"  {type(question).__name__:<22} | {question.question_text[:70]}"
                )


if __name__ == "__main__":
    asyncio.run(main())
