# Talk to an AI model that is running on external servers

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
while True:
    query = input("Ask Query: ")

    if query == "q":
        break

    client = OpenAI()
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=query
    )

    print("AI response: ",response.output_text)
