import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
load_dotenv()




base_model = init_chat_model(
    model= "openai/gpt-oss-120b",
    model_provider= 'groq',
    temperature = 0.2,
    api_key = os.getenv("GROQ_API_KEY")

)




if __name__ == "__main__":
    
    response = base_model.invoke("what is the capital of India?").content

    print(response)