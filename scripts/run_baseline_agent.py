from app.agents.baseline_agent import (
    BaselineAgent,
)


def main():

    print(
        "\n"
        "================================"
    )

    print(
        " EnterpriseOps Baseline Agent"
    )

    print(
        "================================"
    )

    print(
        "Type 'exit' or 'quit' to stop."
    )

    agent = BaselineAgent()

    while True:

        user_input = input(
            "\nUser: "
        ).strip()

        if not user_input:
            continue

        if user_input.lower() in {
            "exit",
            "quit",
        }:
            break

        try:

            answer = agent.run(
                user_input
            )

            print(
                f"\nAgent:\n{answer}"
            )

        except Exception as exc:

            print(
                "\nAgent Error:"
            )

            print(exc)


if __name__ == "__main__":
    main()