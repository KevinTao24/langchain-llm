import json
import uuid

import requests
import streamlit as st


def handle_response_line(line):
    """处理响应中的每一行数据"""
    decoded_line = line.decode("utf-8")
    if decoded_line.startswith("data: "):
        return handle_data_line(decoded_line)
    elif decoded_line.startswith("event: ") or ": ping" in decoded_line:
        return None  # 忽略事件和ping消息
    else:
        return f"{decoded_line}"  # 对于普通文本行，添加换行符


def handle_data_line(decoded_line):
    """处理以'data: '开头的行"""
    json_data = decoded_line[len("data: ") :]
    try:
        data = json.loads(json_data)
        return process_event_data(data)
    except json.JSONDecodeError as e:
        return f"JSON decoding error: {e}\n\n"


def process_event_data(data):
    """处理事件数据"""
    if "event" in data:
        return handle_event(data)
    elif "content" in data or "steps" in data or "output" in data:
        return f"{data.get('content') or data.get('steps') or data.get('output')}\n"


def handle_event(data):
    """处理特定的事件类型"""
    kind = data["event"]
    if kind == "on_chat_model_stream":
        return (
            data["data"]["chunk"]["content"]
            if data["data"]["chunk"]["content"]
            else None
        )
    elif kind == "on_tool_start":
        return handle_tool_start(data)
    elif kind == "on_tool_end":
        return "Search completed.\n"


def handle_tool_start(data):
    """处理工具开始事件"""
    tool_inputs = data["data"].get("input")
    inputs_str = (
        ", ".join(f"'{v}'" for k, v in tool_inputs.items())
        if isinstance(tool_inputs, dict)
        else str(tool_inputs)
    )
    return f"Searching Tool: {data['name']} with input: {inputs_str} ⏳\n"


def consume_api(url, user_query, session_id):
    """使用requests POST与FastAPI后端通信，支持流式传输。"""
    headers = {"Content-Type": "application/json"}
    config = {"session_id": session_id}
    payload = {"input": user_query, "config": config}

    with requests.post(url, json=payload, headers=headers, stream=True) as response:
        try:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    content = handle_response_line(line)
                    if content:
                        yield content
        except requests.exceptions.HTTPError as err:
            yield f"HTTP Error: {err}\n\n"
        except Exception as e:
            yield f"An error occurred: {e}\n\n"


def call_gemini(message, session_id):
    return consume_api(
        url=f"http://localhost:8000/gemini/stream_events",
        user_query=message,
        session_id=session_id,
    )


def call_chatglm(message, session_id):
    return consume_api(
        url=f"http://localhost:8000/chatglm/stream_events",
        user_query=message,
        session_id=session_id,
    )


def call_chat_langchain(message, session_id):
    url = f"http://0.0.0.0:8001/chat/langchain/invoke"
    session_id = (session_id,)

    headers = {"Content-Type": "application/json"}
    config = {"session_id": session_id}
    payload = {"input": {"question": message}, "config": config}

    with requests.post(url, json=payload, headers=headers, stream=True) as response:
        try:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    content = handle_response_line(line)
                    if content:
                        yield content
        except requests.exceptions.HTTPError as err:
            yield f"HTTP Error: {err}\n\n"
        except Exception as e:
            yield f"An error occurred: {e}\n\n"


st.title("🚀 问霸霸")

option = "glm-4"
# with st.sidebar:
# option = st.selectbox("Model Selection", ("glm-4", "gemini-pro"))

# if "model" not in st.session_state or st.session_state.model != option:
#     st.session_state.model = option

# st.divider()

# file = st.file_uploader("Upload your file here", accept_multiple_files=False)

# if file and file.type == "application/pdf":
#     print(file)

# st.divider()

# if st.button("Clear History"):
#     st.session_state.messages.clear()
#     st.session_state["messages"] = [
#         {"role": "assistant", "content": "How can I help you today?"}
#     ]
#     st.session_state["session_id"] = str(uuid.uuid4())


if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you today?"}
    ]

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])
if prompt := st.chat_input(key=st.session_state.session_id):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if option == "gemini-pro":
        msg = st.chat_message("assistant").write_stream(
            call_gemini(prompt, st.session_state.session_id)
        )
    elif option == "glm-4":
        msg = st.chat_message("assistant").write_stream(
            call_chatglm(prompt, st.session_state.session_id)
        )
    elif option == "chat_langchain":
        msg = st.chat_message("assistant").write_stream(
            call_chat_langchain(prompt, st.session_state.session_id)
        )
    st.session_state.messages.append({"role": "assistant", "content": msg})
