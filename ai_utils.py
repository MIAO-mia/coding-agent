"""
AI related tool
"""

import json
import re
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS


def extract_json_from_response(response_text):
    """
    Extract JSON content from AI response
    """
    if not response_text:
        return "no_json", None

    try:
        json_data = json.loads(response_text)
        return "success", json_data
    except json.JSONDecodeError:
        pass

    pattern = r'```(?:json)?\s*(.*?)\s*```'
    matches = re.findall(pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            json_data = json.loads(match.strip())
            return "success", json_data
        except json.JSONDecodeError:
            continue

    brace_pattern = r'(\{.*?\})'
    matches = re.findall(brace_pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            json_data = json.loads(match)
            return "success", json_data
        except json.JSONDecodeError:
            continue

    return "no_json", response_text


def get_raw_ai_response(messages,
                        api_key=None,
                        base_url=None,
                        model=None,
                        temperature=None,
                        max_tokens=None,
                        response_type='text'):
    """
    Simple API call returning raw response
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL
    temperature = temperature or DEFAULT_TEMPERATURE
    max_tokens = max_tokens or MAX_TOKENS

    if not api_key:
        return "error", "API key not provided"

    extra_params = {}
    if response_type == 'json_object':
        extra_params['response_format'] = {"type": "json_object"}

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra_params
        )

        full_response = response.choices[0].message.content
        return "success", full_response.strip()

    except Exception as e:
        error_msg = f"API error: {str(e)}"
        return "error", error_msg


def modify_prompt(user_mission, max_tokens=8100, api_key=None, base_url=None, model=None):
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    system_prompt = f"""{user_mission}
    
This is a programming prompt that will be submitted to an coding AI to write Python code. Refine it to make it easy to implement.
Break down the intention, don't add any new features. Rewrite it into a well-structured, detailed, and technically specific one. But don't make it lengthy, keep it simple, and only talk about how to do it explicitly. The core is to instruct clearly.
Please output the prompt directly."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_mission}
    ]
    status, response = get_raw_ai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0.5,
        max_tokens=max_tokens
    )

    if status == "error":
        return "error", response
    else:
        return "success", response


def get_first_response(code_mission, api_key=None, base_url=None, model=None):
    """
    Get the complete project structure at once, including project_folder_name
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    complete_prompt = f"""You are an experienced software architect. Here is a program task:

{code_mission}

Break down the task, and write robust code.
With Python as the primary programming language, you need to generate a complete project structure, including the file hierarchy and the full code for each file. Please note that the final file to run is main.py, so the main file must be named main.py.

**Important:**
1. Based on the project type, you must specify in the "project_type" field:
   - If it's a web application (e.g., Flask, Django, FastAPI, etc.), use "web"
   - If it's a command-line tool, script, desktop application, etc., use "python"

2. You need to assign an appropriate folder name for this project in the "project_folder_name" field.
   - The name should be concise, meaningful, and use lowercase letters, numbers, and underscores.
   - Do not include Chinese characters, spaces, or special characters.

3. In the "description" field, please provide a detailed record of the core information of the code.

You output should strictly follow the json format. Below is an example:
{{
    "project_folder_name": "code_mission",  // folder name for the project
    "project_type": "web",  // or "python". choose it based on the type of the project.
    "out_file": [
        {{
            "file_name": "main.py",
            "operation": "write",  //if you want to modify the code or add new file, choose "write". if you want to delete the file, choose "delete", and you can leave "code" empty.
            "description": "Main program file, containing the program entry point and main logic...",  // Do not write what you have added, but what is this code about right now.
            "code": "Complete Python code, including import, function definition and main function etc."
        }},
        {{
            "file_name": "requirements.txt",
            "operation": "write",
            "description": "……",
            "code": "……"
        }},
        {{
            "file_name": "sub_folder/code.py",
            "operation": "write",
            "description": "……",
            "code": "Complete Python code……"
        }}
    ]
}}"""

    messages = [
        {"role": "user", "content": complete_prompt}
    ]

    status, response = get_raw_ai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        response_type='json_object'
    )

    if status == "error":
        return "error", response, messages

    json_status, json_data = extract_json_from_response(response)

    if json_status == "success":
        messages.append({"role": "assistant", "content": response})
        return "success", json_data, messages
    else:
        error_msg = f"can't recognize as JSON: {json_data}"
        return "error", error_msg, messages


def get_error_response(former_message, error_message, api_key=None,
                       base_url=None,
                       model=None):
    """
    Fix project error messages
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    complete_prompt = f"""The code has some errors:
{error_message}
Please identify which files need to be modified, and write code for the related files.
Note: Every single code should be complete, not just pieces of it, and your output should follow the previous json format."""

    former_message.append({"role": "user", "content": complete_prompt})
    status, response = get_raw_ai_response(
        messages=former_message,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        response_type='json_object'
    )
    if status == "error":
        return "error", response, former_message

    json_status, json_data = extract_json_from_response(response)

    if json_status == "success":
        former_message.append({"role": "assistant", "content": response})
        return "success", json_data, former_message
    else:
        error_msg = f"can't recognize as JSON: {json_data}"
        return "error", error_msg, former_message


def get_modify_response(former_message, modify_message, api_key=None,
                        base_url=None,
                        model=None):
    """
    modify based on users input
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    complete_prompt = f"""I need you for some modifications:
{modify_message}
please identify which files need to be modified, and write code for the related files.
Note: Every single code should be complete, not just pieces of it, and your output should follow the previous json format."""

    former_message.append({"role": "user", "content": complete_prompt})
    status, response = get_raw_ai_response(
        messages=former_message,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        response_type='json_object'
    )
    if status == "error":
        return "error", response, former_message

    json_status, json_data = extract_json_from_response(response)

    if json_status == "success":
        former_message.append({"role": "assistant", "content": response})
        return "success", json_data, former_message
    else:
        error_msg = f"can't recognize as JSON: {json_data}"
        return "error", error_msg, former_message


def get_project_response(code_mission, project_structure, api_key=None, base_url=None, model=None):
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    complete_prompt = f"""You are an experienced software architect. Here is the structure of a project:
{project_structure}

Here are some modifications that you need to make to that project:
{code_mission}
Remember to keep the original style and layout unchanged, so read necessary files before writing.
Whenever you think you need more information, choose to read.
When you think you have gathered enough information, you can write code.
**IMPORTANT**
1. Based on the project type, you must specify in the "project_type" field:
   - If it's a web application (e.g., Flask, Django, FastAPI, etc.), use "web"
   - If it's a command-line tool, script, desktop application, etc., use "python"
2. In the "description" field, please provide a detailed record of the core information of the code you write.
3. Only make necessary changes, especially don't change the style and layout of the frontend only when you are told to do so. So remember to read the core codes before writing.
4. You can choose to write and delete at the same time, but you can't choose to read and write or to read and delete.  


You output should strictly follow the json format. READ AND WRITE USE THE SAME FORMAT. Below are two examples:
FOR READ:
{{
    "project_folder_name": "code_mission",  // folder name of the project
    "project_type": "web",  // or "python". choose it based on the type of the project.
    "out_file": [
        {{
            "file_name": "main.py",
            "operation": "read",  //if you want to modify the code or add a new file, choose "write". if you want to delete or read the file, choose "delete" / "read", and you can leave "description" and "code" empty.
            "description": ".
            "code": ""
        }},
        {{
            "file_name": "requirements.txt",
            "operation": "read",
            "description": "……",
            "code": "……"
        }},
        {{
            "file_name": "sub_folder/code.py",
            "operation": "read",
            "description": "……",
            "code": "Complete Python code……"
        }}
    ]
}}

FOR WRITE:
{{
    "project_folder_name": "code_mission",  // folder name of the project
    "project_type": "web",  // or "python". choose it based on the type of the project.
    "out_file": [
        {{
            "file_name": "main.py",
            "operation": "write",  //if you want to modify the code or add a new file, choose "write". if you want to delete or read the file, choose "delete" / "read", and you can leave "description" and "code" empty.
            "description": "Main program file, containing the program entry point and main logic...",  // Do not write what you have added, but what is this code about right now.
            "code": "Complete Python code, including import, function definition and main function etc."
        }},
        {{
            "file_name": "requirements.txt",
            "operation": "write",
            "description": "……",
            "code": "……"
        }},
        {{
            "file_name": "sub_folder/code.py",
            "operation": "write",
            "description": "……",
            "code": "Complete Python code……"
        }}
    ]
}}
Remember: READ FIRST, WRITE LATER"""

    messages = [
        {"role": "user", "content": complete_prompt}
    ]
    status, response = get_raw_ai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        response_type='json_object'
    )

    if status == "error":
        return "error", response, messages

    json_status, json_data = extract_json_from_response(response)

    if json_status == "success":
        messages.append({"role": "assistant", "content": response})
        return "success", json_data, messages
    else:
        error_msg = f"can't recognize as JSON: {json_data}"
        return "error", error_msg, messages


def code_detail_feedback(former_message, code_detail, api_key=None, base_url=None, model=None):
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    complete_prompt = f"""Here are the code details you request:
{code_detail}
If you need more code, make another request. If you want write code, output directly.
Remember: only make the necessary modification. Especially don't change the style and layout of the frontend only when you are told to do so.
Use the previously mentioned json format.
"""

    former_message.append({"role": "user", "content": complete_prompt})
    status, response = get_raw_ai_response(
        messages=former_message,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        response_type='json_object'
    )

    if status == "error":
        return "error", response, former_message

    json_status, json_data = extract_json_from_response(response)

    if json_status == "success":
        former_message.append({"role": "assistant", "content": response})
        return "success", json_data, former_message
    else:
        error_msg = f"can't recognize as JSON: {json_data}"
        return "error", error_msg, former_message
