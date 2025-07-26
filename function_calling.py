import json
import math
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


def calculate_circle_area(radius):
    area = math.pi * radius * radius
    print(f"radius: {radius}, area: {area}")
    return math.pi * radius * radius


function_schema = [
    {
        "name": "func_1",
        "description": "This is what the function does and this is when the function should be called.",
        "parameters": {
            "type": "object",
            "properties": {
                "argument_1": {"type": "data_type", "description": "What argument_1 is and its description"}
            },
            "required": ["argument_1"],
        },
    }
]


def func_1(argument_1):
    return argument_1 * 2


function_schema = [
    {
        "name": "calculate_circle_area",
        "description": "Calculate the area of a circle given the radius.",
        "parameters": {
            "type": "object",
            "properties": {"radius": {"type": "number", "description": "The radius of the circle in centimeters."}},
            "required": ["radius"],
        },
    }
]

user_message = "Calculate the area of a circle with a radius of five meters."

client = AzureOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), api_version="2024-07-01-preview", azure_endpoint=os.getenv("OPENAI_API_HOST")
)


response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": user_message}],
    functions=function_schema,
    function_call="auto",
)

message = response.choices[0].message

if hasattr(message, "function_call"):
    function_name = message.function_call.name
    arguments = json.loads(message.function_call.arguments)

    if function_name == "calculate_circle_area":
        radius = arguments.get("radius")
        area = calculate_circle_area(radius)

        # Convert the result to a string to send back to the model
        function_response = str(area)

        # Send the result back to the model
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_message},
                message,
                {"role": "function", "name": function_name, "content": function_response},
            ],
        )

        final_answer = second_response.choices[0].message.content
        print("Message:", message)
        print("final_answer:", final_answer)
else:
    # If no function call is made, just print the assistant's response
    print(message["content"])
