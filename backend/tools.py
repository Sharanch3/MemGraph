import os
import requests
from backend.base_model import model
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_experimental.tools import PythonREPLTool
from dotenv import load_dotenv
load_dotenv()



#WEATHER API
@tool
def fetch_weather(place: str) ->dict:
    """Retrieve current weather information for the specified city or location."""
    
    url = f"http://api.weatherapi.com/v1/current.json?key={os.getenv('API_KEY')}&q={place}"

    response = requests.get(url= url)

    return response.json()



#STOCK API
@tool
def get_stock_price(symbol: str) ->dict:
    """
    Fetch latest stock price for the given symbol. e.g - ['APPL', 'TSLA']
    using Alpha Vantage with API key in the URL.

    """

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('STOCK_API')}"

    response = requests.get(url)

    return response.json()



#PRECISE COMPUTATION
python_tool = PythonREPLTool()



#WEB SEARCH
search_tool = TavilySearch(
    max_results = 2,
    topic = "general"
)



#Tool Binding
tools = [fetch_weather, get_stock_price, python_tool, search_tool]

model_with_tools = model.bind_tools(tools= tools, tool_choice= "auto")