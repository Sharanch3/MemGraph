import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()


model = init_chat_model(
    model= "openai/gpt-oss-120b",
    model_provider= "groq",
    temperature = 0.2,
    api_key = os.getenv("GROQ_API_KEY")

)
