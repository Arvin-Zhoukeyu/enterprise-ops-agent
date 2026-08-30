from app.agents.workflow.agent import (
    WorkflowAgent,
)


def main():

    print(
        "\n"
        "================================"
    )

    print(
        " EnterpriseOps Workflow Agent"
    )

    print(
        "================================"
    )

    agent = WorkflowAgent()

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
                f"\nAgent Error:\n{exc}"
            )


if __name__ == "__main__":
    main()