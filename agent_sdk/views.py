import os
import json
import base64
import asyncio
from openai import OpenAI
from django.shortcuts import render
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse

from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner

def ui(request):
    return render(request, 'agent_sdk/chatUI.html')

@csrf_exempt
def response_api(request):

    # payload
    data = json.loads(request.body)

    # OAI key
    openai_key = os.environ["OAI_KEY"]
    client = OpenAI(api_key=openai_key)

    # text generation
    # response = client.responses.create(
    #     model = "o3-mini",
    #     input = data.get("message")
    # )
    # result = response.output_text

    # multimodal input (text + image)
    # image_url = "https://upload.wikimedia.org/wikipedia/commons/3/3b/LeBron_James_Layup_%28Cleveland_vs_Brooklyn_2018%29.jpg"
    # response = client.responses.create(
    #     model = "gpt-4o",
    #     input = [
    #         {
    #             "role": "user",
    #             "content": "what teams are playing in this image? What is this bball league?"
    #         },
    #         {
    #             "role": "user",
    #             "content": [{"type": "input_image", "image_url": image_url}]
    #         }
    #     ]
    # )
    # result = response.output_text

    # tools (web search)
    response = client.responses.create(
        model = "gpt-4o",
        tools = [{"type": "web_search_preview"}],
        input = data.get("message"),
    )
    result = response.output_text

    # tools (file search)
    # response = client.responses.create(
    #     model = "gpt-4o",
    #     input = data.get("message"),
    #     tools = [{
    #         "type": "file_search",
    #         "vector_store_ids": [os.environ["OAI_VECTOR_DEV_V1"]]
    #     }]
    # )
    # result = response.output_text

    # multimodal & web-search
    # url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/2880px-Cat_August_2010-4.jpg"
    # response = client.responses.create(
    #     model = "gpt-4o",
    #     input = [{
    #                 "role":"user",
    #                 "content": [
    #                     {"type": "input_text", "text": data.get("message")},
    #                     {"type": "input_image", "image_url": url}
    #                 ]
    #             }],
    #     tools = [{"type" : "web_search"}]
    # )
    # result = response.output_text

    return HttpResponse(result, content_type="text/markdown")

@csrf_exempt
def agent_sdk(request):
    # payload
    data = json.loads(request.body)

    # OAI key
    os.environ["OPENAI_API_KEY"] = os.environ["OAI_KEY"]

    # agent
    agent = Agent(
        name = "History Tutor",
        handoff_description="Specialized agent for historical questions",
        instructions= "You provide assistance with historical queries. Explain important events and context clearly."
    )

    async def _async_task():
        result = await Runner.run(agent, data.get("message"))
        return result
    response = async_to_sync(_async_task)()
    result = response.final_output

    return HttpResponse(result, content_type="text/markdown") 
