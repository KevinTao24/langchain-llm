from typing import List, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_models.zhipuai import ChatZhipuAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langserve import add_routes

from future.chains.langchain_chain import ChatInput, answer_chain
from future.my_secrets import GOOGLE_API_KEY, ZHIPU_API_KEY

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

add_routes(
    app,
    answer_chain.with_types(input_type=ChatInput),
    path="/chat/langchain",
    config_keys=["metadata", "configurable", "tags"],
)

chat_glm = ChatZhipuAI(
    model="glm-4",
    temperature=0.5,
    api_key=ZHIPU_API_KEY,
)

add_routes(app, chat_glm, path="/chat/glm", playground_type="chat")


# Declare a chain
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful, professional assistant named Cob."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# chain = prompt | chat


# class InputChat(BaseModel):
#     """Input for the chat endpoint."""

#     messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = Field(
#         ...,
#         description="The chat messages representing the current conversation.",
#     )


# add_routes(
#     app,
#     chain.with_types(input_type=InputChat),
#     enable_feedback_endpoint=True,
#     enable_public_trace_link_endpoint=True,
#     playground_type="chat",
# )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
