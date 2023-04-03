# Automated Code Review using the ChatGPT language model

## Import statements
import argparse
import openai
import os
import requests
import re
from github import Github

## Adding command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--openai_api_key', help='Your OpenAI API Key')
parser.add_argument('--github_token', help='Your Github Token')
parser.add_argument('--github_pr_id', help='Your Github PR ID')
parser.add_argument('--openai_engine', default="text-davinci-002", help='GPT-3 model to use. Options: text-davinci-002, text-babbage-001, text-curie-001, text-ada-001')
parser.add_argument('--openai_temperature', default=0.5, help='Sampling temperature to use. Higher values means the model will take more risks. Recommended: 0.5')
parser.add_argument('--openai_max_tokens', default=2048, help='The maximum number of tokens to generate in the completion.')
args = parser.parse_args()

## Authenticating with the OpenAI API
openai.api_key = args.openai_api_key

## Authenticating with the Github API
g = Github(args.github_token)
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
pull_request = repo.get_pull(int(args.github_pr_id))
branch = pull_request.head
CONTROLLER = "Controller.java"

# The send_to_chat_gpt function takes three arguments:
#
# command: a string that represents the command or action to be performed
# file_name: a string that represents the name of the file
# file_content: a string that represents the content of the file
# The function makes use of the OpenAI API by calling the openai.Completion.create() method.
# The output of the function is a string that represents ChatGPT's response about the file.
def send_to_chat_gpt(command, file_content):
    print(f"Command sent to chatgpt:\n\n{command}:\n```{file_content}```\n")
    response = openai.Completion.create(
        engine=args.openai_engine,
        prompt=(f"{command}:\n```{file_content}```"),
        temperature=float(args.openai_temperature),
        max_tokens=int(args.openai_max_tokens)
    )
    print(f"Raw Response: \n{response}\n")
    
    return response['choices'][0]['text']

def compile_overview_description(generated_stoplight):
    summary = send_to_chat_gpt("Summarize this", generated_stoplight)
    pattern = r"description: .*?\n"
    replacement = f"description: |\n      {summary}\n"
    
    return re.sub(pattern, replacement, generated_stoplight, count=1)

def compile_stoplight_doc(command, file_name, file_content):
    # Get the structure
    response_content = send_to_chat_gpt(command, file_content)

    response_content = f"```yaml\n{response_content}\n```"
    print(f"Result from chat gpt:\n\n{file_name}`:\n ```yaml{response_content}```\n")
    
    # Polishing the response with proper metadata and format
    index = response_content.index("paths:")
    replaced_with = f"openapi: 3.1.0\ninfo:\n    title: {file_name}\n    description: \n    version: '1.0'\nservers:\n    - url: 'http://localhost:3000'\n"
    response_content =  replaced_with + response_content[index:]

    # Compile the Overview Description
    response_content = compile_overview_description(response_content)

    print(f"Updated response from chat gpt:\n\n{file_name}`:\n {response_content}\n")
   
    # Adding a comment to the pull request with ChatGPT's response
    pull_request.create_issue_comment(
        f"ChatGPT's response about `{file_name}`:\n ```yaml{response_content}```")

    return response_content

def get_content_patch():
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/pulls/{args.github_pr_id}"
    print(url)

    headers = {
        'Authorization': f"token {args.github_token}",
        'Accept': 'application/vnd.github.v3.diff'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        raise Exception(response.text)

    return response.text

def push_changed_files_to_pr(file_changes):
    for file in file_changes:
        file_name = file["name"]
        filename = f"{file_name}.yaml"
        try:
            # Find the existing file
            existing_file = repo.get_contents(filename, branch.sha)
            # Update file
            repo.update_file(
                path=filename,
                message=f"Chore: update generated stoplight {filename}",
                content=file["content"],
                sha= existing_file.sha,
                branch=branch.ref
            )
        
        except Exception:
            # Create the new file
            repo.create_file(
                path=filename,
                message=f"Chore: add generated stoplight file {filename}",
                content=file["content"],
                branch=branch.ref
            )

def create_stoplight_doc():
    content = get_content_patch()

    if len(content) == 0:
        pull_request.create_issue_comment("Patch file does not contain any changes")
        return

    parsed_text = content.split("diff")
    file_changes = []

    for diff_text in parsed_text:
        if len(diff_text) == 0:
            continue

        try:
            file_name = diff_text.split("b/")[1].splitlines()[0]
            print(f"File name: {file_name}")
            is_controller = file_name.endswith(CONTROLLER)
            print(f"Contains Controller.java: {is_controller}")
            if is_controller:
                response = compile_stoplight_doc("Generate a Stoplight API documentation in YAML file format", file_name, diff_text)
                yaml_name = file_name.replace(CONTROLLER, "")
                file_changes.append({ "name": yaml_name, "content": response })

        except Exception as e:
            error_message = str(e)
            print(error_message)
            pull_request.create_issue_comment(f"ChatGPT was unable to process the response about {error_message}")

    push_changed_files_to_pr(file_changes)

print("main.py is running")

create_stoplight_doc()
