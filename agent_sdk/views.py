import os
import json
import base64
import asyncio
from openai import OpenAI
from pydantic import BaseModel
from django.shortcuts import render
from IPython.display import Image, display
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, StreamingHttpResponse
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner


def ui(request):
    return render(request, 'agent_sdk/chatUI.html')

@csrf_exempt
def chat(request):

    # payload
    data = json.loads(request.body)
    message = data.get("message", "") 

    # OAI key
    openai_key = os.environ["OAI_KEY"]
    client = OpenAI(api_key=openai_key)

    # text generation
    # response = client.responses.create(
    #     model = "o3-mini",
    #     input = "Wwhat model are you"
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
        input = message,
    )
    result = response.output_text


    return HttpResponse(result, content_type="text/markdown")
