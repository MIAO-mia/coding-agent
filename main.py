from agent import run_project, error_project, modify_project, project_project, generate_project
import os

def main1(prompt):
    # First generation
    code_first_result = generate_project(code_mission=prompt)
    print()
    print("\n=== Running project ===")
    run_first_result = run_project(result=code_first_result)
    print(run_first_result)
    error_message = run_first_result.get("error", "")
    round_messages = code_first_result.get("messages")
    code_round_result = None

    # Handle errors after first generation
    while error_message:
        code_round_result = error_project(former_message=round_messages, error_message=error_message)

        run_round_result = run_project(result=code_round_result)

        error_message = run_round_result.get("error", "")
        round_messages = code_round_result.get("messages")

    # Enter user interaction loop
    print("\n" + "=" * 50)
    print("The project is successfully generated! Now you can make more modifications.")
    print("Type 'exit' to exit")
    print("=" * 50)

    while True:
        # Get user input
        user_input = input("\nType your modification need or type 'exit' to exit:").strip()

        if user_input.lower() == 'exit':
            break

        elif user_input:
            # User has new modification requirements
            print(f"\n=== Handling your need: {user_input} ===")

            # Get current messages
            current_messages = (code_round_result.get("messages")
                                if code_round_result
                                else code_first_result.get("messages"))

            # Modify project
            modify_result = modify_project(former_message=current_messages, modify_message=user_input
            )

            # Run modified project
            print("\n=== Running modified project ===")
            run_result = run_project(result=modify_result)

            # Handle potential errors
            error_message = run_result.get("error", "")
            if error_message:
                print("Discovered errors, starting to fix...")
                current_messages = modify_result.get("messages")

                while error_message:
                    code_round_result = error_project(former_message=current_messages,error_message=error_message)
                    run_result = run_project(result=code_round_result)
                    error_message = run_result.get("error", "")
                    current_messages = code_round_result.get("messages")
            else:
                # If no errors, update code_round_result for next modification
                code_round_result = modify_result

        else:
            print("Please type valid content, or type 'exit' to exit")

def main2(prompt, project_folder):
    # First generation
    code_first_result = project_project(code_mission=prompt, project_folder=project_folder)
    parent_folder = os.path.dirname(project_folder)
    print()
    print("\n=== Running project ===")
    run_first_result = run_project(result=code_first_result)
    print(run_first_result)
    error_message = run_first_result.get("error", "")
    round_messages = code_first_result.get("messages")
    code_round_result = None

    # Handle errors after first generation
    while error_message:
        code_round_result = error_project(former_message=round_messages, error_message=error_message,
                                          project_root=parent_folder)

        run_round_result = run_project(result=code_round_result)

        error_message = run_round_result.get("error", "")
        round_messages = code_round_result.get("messages")

    # Enter user interaction loop
    print("\n" + "=" * 50)
    print("The project is successfully generated! Now you can make more modifications.")
    print("Type 'exit' to exit")
    print("=" * 50)

    while True:
        # Get user input
        user_input = input("\nType your modification need or type 'exit' to exit:").strip()

        if user_input.lower() == 'exit':
            break

        elif user_input:
            # User has new modification requirements
            print(f"\n=== Handling your need: {user_input} ===")

            # Get current messages
            current_messages = (code_round_result.get("messages")
                                if code_round_result
                                else code_first_result.get("messages"))

            # Modify project
            modify_result = modify_project(former_message=current_messages, modify_message=user_input
                                           , project_root=parent_folder)
            print(modify_result.get("messages"))
            # Run modified project
            print("\n=== Running modified project ===")
            run_result = run_project(result=modify_result)

            # Handle potential errors
            error_message = run_result.get("error", "")
            if error_message:
                print("Discovered errors, starting to fix...")
                current_messages = modify_result.get("messages")

                while error_message:
                    code_round_result = error_project(former_message=current_messages, error_message=error_message,
                                                      project_root=parent_folder)
                    run_result = run_project(result=code_round_result)
                    error_message = run_result.get("error", "")
                    current_messages = code_round_result.get("messages")
            else:
                # If no errors, update code_round_result for next modification
                code_round_result = modify_result

        else:
            print("Please type valid content, or type 'exit' to exit")


if __name__ == "__main__":
    print("The program has two mode")
    print("1. generate a project from nothing")
    print("2. modify existing project")
    mode_num = input("type 1 or 2 to choose mode\n")
    if str(mode_num) == "1":
        prompt1 = input("Tell me your coding demand:\n")
        main1(prompt1)
    elif str(mode_num) == "2":
        prompt2 = input("Tell me your modification demand:\n")
        project_folder = input("Tell me the path of your existing project:\n")
        main2(prompt2, project_folder)
