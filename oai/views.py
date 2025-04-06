import os
import json
from openai import OpenAI
from django.shortcuts import render
from langchain_openai import ChatOpenAI
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, StreamingHttpResponse

def ui(request):
    return render(request, 'oai/chatUI.html')

def event_stream(llm, messages):
    full_content = ''
    for chunk in llm.stream(messages):
        content = chunk.content
        full_content += content
        print(content)
        yield f"data: {json.dumps({'content': content})}\n\n"
    yield f"data: {json.dumps({'content': '', 'is_final': True})}\n\n"

@csrf_exempt
def chat_langchain(request):
    # payload
    payload = request.body.decode('utf-8')
    payload = json.loads(payload)

    # message
    msg = payload.get('message')
    messages=[{"role": "user", "content": msg}]

    # model
    llm = ChatOpenAI(
        organization=os.getenv("OAI_ORG_ID"),
        api_key=os.getenv("OAI_KEY"),
        model="o3-mini",
    )

    # stream response
    return StreamingHttpResponse(event_stream(llm, messages), content_type="text/event-stream")
