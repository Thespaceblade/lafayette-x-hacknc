"""Print the weekend replay without the web server.

Run: python -m app.replay
"""

from __future__ import annotations

from app.session import Session


def main() -> None:
    session = Session()
    session.replay()
    inbox = session.inbox()
    print(
        f"{inbox['count']} messages | Gemini calls {inbox['gemini_calls']} | "
        f"no LLM {inbox['no_llm_calls']}"
    )
    print(f"routes: {inbox['by_route']}")
    for result in inbox["messages"]:
        confidence = result["classification"]["confidence"]
        confidence_text = "n/a" if confidence is None else f"{confidence:.2f}"
        link = result["linked_to"] or "-"
        print(
            f"{result['message_id']} {result['route']:<22} "
            f"gemini={str(result['gemini_called']):<5} "
            f"link={link:<4} conf={confidence_text} "
            f"deadline={result['deadline']}"
        )
    overdue = session.overdue()
    print(f"overdue at {overdue['as_of']}: {overdue['count']}")
    stats = session.stats()
    under = stats["under_1_hour"]
    over = stats["over_24_hours"]
    print(
        f"tours under 1h: {under['tours']} of {under['total']}; "
        f"over 24h: {over['tours']} of {over['total']} ({stats['source']})"
    )


if __name__ == "__main__":
    main()
