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
HISTORY_TOURNAMENTS = {
    "minibench": "minibench",
    "summer-futureeval-2026": 33022,
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

    # Past questions show the cadence: when questions opened and how long they stayed open.
    for name, tournament_id in HISTORY_TOURNAMENTS.items():
        api_filter = ApiFilter(
            allowed_tournaments=[tournament_id],
            allowed_statuses=["closed", "resolved"],
            group_question_mode="unpack_subquestions",
        )
        try:
            questions = await client.get_questions_matching_filter(
                api_filter, error_if_question_target_missed=False
            )
        except Exception as error:  # noqa: BLE001
            print(f"\n{name} [history]: error {type(error).__name__}: {error}")
            continue
        timed = [q for q in questions if q.open_time and q.close_time]
        timed.sort(key=lambda q: q.open_time)
        print(f"\n{name} [closed+resolved]: {len(questions)} questions")
        if not timed:
            continue
        hours_open = sorted(
            (q.close_time - q.open_time).total_seconds() / 3600 for q in timed
        )
        print(
            f"  first opened {timed[0].open_time:%Y-%m-%d}, last opened "
            f"{timed[-1].open_time:%Y-%m-%d %H:%M}; hours open: min "
            f"{hours_open[0]:.1f}, median {hours_open[len(hours_open) // 2]:.1f}, "
            f"max {hours_open[-1]:.1f}"
        )
        opens_per_day: dict[str, int] = {}
        for question in timed:
            day = f"{question.open_time:%Y-%m-%d}"
            opens_per_day[day] = opens_per_day.get(day, 0) + 1
        last_days = sorted(opens_per_day.items())[-10:]
        print("  questions opened per day (last 10 days with questions): " + ", ".join(
            f"{day} {count}" for day, count in last_days
        ))
        for question in timed[-3:]:
            print(
                f"  opens {question.open_time:%Y-%m-%d %H:%M} | closes "
                f"{question.close_time:%Y-%m-%d %H:%M} | {question.question_text[:60]}"
            )


if __name__ == "__main__":
    asyncio.run(main())
