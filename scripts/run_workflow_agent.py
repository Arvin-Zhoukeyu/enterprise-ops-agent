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

        if user_input.lower() in {
            "exit",
            "quit",
        }:
            break

        role = input(
            "Role "
            "(employee/manager/admin): "
        ).strip()

        if not role:

            role = "employee"

        try:

            response = agent.run(
                user_input=user_input,
                user_role=role,
            )

            thread_id = (
                response[
                    "thread_id"
                ]
            )

            result = (
                response["result"]
            )

            print(
                f"\nThread ID: "
                f"{thread_id}"
            )

            if (
                "__interrupt__"
                in result
            ):

                print(
                    "\nApproval required."
                )

                decision = input(
                    "Approve? "
                    "(yes/no): "
                ).strip().lower()

                approved = (
                    decision
                    in {
                        "yes",
                        "y",
                    }
                )

                result = agent.resume(
                    thread_id=thread_id,
                    approved=approved,
                )

            final_answer = (
                result.get(
                    "final_answer",
                    ""
                )
            )

            print(
                f"\nAgent:\n"
                f"{final_answer}"
            )

        except Exception as exc:

            print(
                f"\nAgent Error:\n"
                f"{exc}"
            )


if __name__ == "__main__":
    main()