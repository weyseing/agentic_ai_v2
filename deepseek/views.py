import os
import json
from django.shortcuts import render
from langchain_core.messages import HumanMessage
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, StreamingHttpResponse
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel

def ui(request):
    return render(request, 'deepseek/chatUI.html')

@csrf_exempt
def chat(request):
    # payload
    payload = request.body.decode('utf-8')
    payload = json.loads(payload)

    # message
    msg = payload.get('message')
    messages = [HumanMessage(content=msg)]

    # deepseek
    model = AzureAIChatCompletionsModel(
        endpoint=os.getenv('DEEPSEEK_ENDPOINT'),
        credential=os.getenv('DEEPSEEK_KEY'),
        model_name="DeepSeek-R1",
        temperature=0.1,
        top_p=0.5,
        max_tokens=5000,
    )

    def event_stream():
        for chunk in model.stream(messages):
            content = chunk.content
            print(content)
            yield f"data: {json.dumps({'content': content})}\n\n"
        yield f"data: {json.dumps({'content': '', 'is_final': True})}\n\n"

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


