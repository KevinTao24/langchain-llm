from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

chat = ChatZhipuAI(
    model="glm-4",
    temperature=0.5,
    api_key="",
)


chat.invoke(
    [
        HumanMessage(
            content="Translate this sentence from English to Chinese: I love programming."
        )
    ]
)

chat.invoke(
    [
        HumanMessage(
            content="Translate this sentence from English to Chinese: I love programming."
        ),
        AIMessage(content="我喜欢编程。"),
        HumanMessage(content="What did you just say?"),
    ]
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

print()


from langsmith.wrappers import wrap_openai
