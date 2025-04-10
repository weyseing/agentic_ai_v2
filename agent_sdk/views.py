import os
import sys
import json
import queue
import base64
import asyncio
import logging
import tempfile
import subprocess
from openai import OpenAI
from pydantic import BaseModel
import matplotlib.pyplot as plt
from django.conf import settings
from django.shortcuts import render
from asgiref.sync import async_to_sync
from django.http import StreamingHttpResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner, WebSearchTool, function_tool, InputGuardrailTripwireTriggered, RunContextWrapper, TResponseInputItem, input_guardrail, output_guardrail
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse

# logging
logging.basicConfig(level=logging.INFO)

def ui(request):
    return render(request, 'agent_sdk/chatUI.html')

def ui_stream(request):
    return render(request, 'agent_sdk/chatUI_stream.html')

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

# @csrf_exempt
async def agent_sdk(request):
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

    response = await Runner.run(agent, data.get("message"))
    result = response.final_output
    
    return HttpResponse(result, content_type="text/markdown") 

@function_tool
def data_visualization_tool(query: str) -> str:
    """
    Generates a line chart and automatically runs collectstatic
    
    Args:
        query (str): Chart title and context identifier [[2]]
    
    Process:
    1. Creates visualization using matplotlib best practices [[3]][[4]]
    2. Saves to STATICFILES_DIRS for development [[5]]
    3. Runs collectstatic to update production static files [[1]][[6]]
    """
    x = [1, 2, 3, 4, 5]
    y = [2, 3, 5, 7, 11]
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker='o', linestyle='-', color='b')
    plt.title(f"Line Chart: {query}")
    plt.xlabel("X-axis (Time Period)")
    plt.ylabel("Y-axis (Value)")
    plt.grid(True)
    filename = os.path.join(settings.STATICFILES_DIRS[0], "line_chart.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    call_command('collectstatic', '--noinput')
    return f"Generated line chart saved as http://localhost:5557/static/line_chart.png"

@csrf_exempt
async def agent_sdk_stream(request):
    # payload
    data = json.loads(request.body)

    # OAI key
    os.environ["OPENAI_API_KEY"] = os.environ["OAI_KEY"]

    # 1st agent
    agent_tech = Agent(
        name="Tech Lead",
        handoff_description="Specialized agent for solve technical questions",
        instructions="You provide assistance with technical queries. Explain step by step in detailed. You seach online web for references.",
        tools=[WebSearchTool()], 
    )

    # 2nd agent
    agent_data_science = Agent(
        name = "Data Science",
        handoff_description= "Specialist agent for data science instrucitons",
        instructions="Use the python_execution tool for visualizations. Explain code step-by-step and include generated images.",
        tools=[data_visualization_tool],
    )

    # triage agent
    triage_agent = Agent(
        name = "Triage Agent",
        instructions="Handoff to the appropriate agent based on the nature of the request",
        handoffs=[agent_tech, agent_data_science]
    )
    
    result = Runner.run_streamed(triage_agent, input=data.get("message"))
    async def event_stream():
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield event.data.delta.encode('utf-8') 

    return StreamingHttpResponse(event_stream(), content_type="text/plain")


@csrf_exempt
async def guardrail(request):
    # reference: https://openai.github.io/openai-agents-python/guardrails/

    # payload
    data = json.loads(request.body)

    # OAI key
    os.environ["OPENAI_API_KEY"] = os.environ["OAI_KEY"]

    # === input guardrail ===
    class DataAnlyticsInput(BaseModel):
        is_data_analytics: bool
        reasoning: str

    guardrail_agent = Agent(
        name = "Guardrail Check",
        model = "o3-mini",
        instructions="Determine whether the user's query is exclusively related to data analytics.",
        output_type= DataAnlyticsInput
    )

    @input_guardrail
    async def data_analytics_guardrail(ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output, 
            tripwire_triggered=not result.final_output.is_data_analytics,
        )
    
    # === agents ====
    # 1st agent
    agent_tech = Agent(
        name="Tech Lead",
        model = "gpt-4o",
        handoff_description="Specialized agent for solve technical questions",
        instructions="You provide assistance with technical queries. Explain step by step in detailed. You seach online web for references.",
        tools=[WebSearchTool()], 
    )

    # 2nd agent
    agent_data_science = Agent(
        name = "Data Science",
        model = "o3-mini",
        handoff_description= "Specialist agent for data science instrucitons",
        instructions="Use the python_execution tool for visualizations. Explain code step-by-step and include generated images.",
        tools=[data_visualization_tool],
    )

    # triage agent
    triage_agent = Agent(
        name = "Triage Agent",
        model = "o3-mini",
        instructions="Handoff to the appropriate agent based on the nature of the request",
        handoffs=[agent_tech, agent_data_science],
        input_guardrails=[data_analytics_guardrail],
    )

    # stream response
    result = Runner.run_streamed(triage_agent, input=data.get("message"))
    async def event_stream():
        try:
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield event.data.delta.encode('utf-8')
        except InputGuardrailTripwireTriggered:
            error_data = {"status": "error", "error_msg":"Request blocked: Outside system safety guidelines"}
            yield f"ERROR_START{json.dumps(error_data)}ERROR_END".encode('utf-8')
            return 

    return StreamingHttpResponse(event_stream(), content_type="text/plain")