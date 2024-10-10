from typing import List
from llama_index.tools.tavily_research import TavilyToolSpec
# from llama_index.utils.workflow import draw_all_possible_flows
from llama_index.core.tools import FunctionTool
from workflows.workflow import FunctionCallingAgent
from workflows.workflow_rag import SubQuestionQueryEngine, prepare_query_engine
from llama_index.llms.openai import OpenAI
from pydantic import Field
from exa_py import Exa
from dotenv import load_dotenv
import datetime
import os 

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
news_api = Exa(api_key=os.getenv("EXA_API_KEY"))


tavily_search = TavilyToolSpec(
    api_key=os.getenv("TAVILY_API_KEY"),
)

def get_news(
        query: str = Field(..., description="The query to search for news"),
    ):
    """
    Use to get news about srilankan politics, in realtime. More realable tool to get latest news

    Args:
        query (str): The query to search for news
    
    Returns:
        List[str]: A list of news articles

    """
    result = news_api.search_and_contents(
        query=query,
        type="neural",
        use_autoprompt=True,
        um_results=10,
        text={
           "max_characters": 400
        },
        start_published_date=datetime.datetime.now().isoformat(), # replace with datetime.datetime.now().isoformat()
        end_published_date=(datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(), # replace with datetime.datetime.now().isoformat()
    )

    return result


async def main(query: str):

    # draw_all_possible_flows(FunctionCallingAgent)
    
    tools = tavily_search.to_tool_list() + [FunctionTool.from_defaults(fn=get_news)]
    

    agent = FunctionCallingAgent(
        llm=OpenAI(model="gpt-4o-mini"), tools=tools, timeout=120, verbose=True
    )

    ret = await agent.run(input=query)

    return ret['response']


qt = None 

async def rag_main(query: str):

    # draw_all_possible_flows(SubQuestionQueryEngine, "workflow_rag.html")

    if qt is None:
        qt = prepare_query_engine("documents")
        
    engine = SubQuestionQueryEngine(timeout=120, verbose=True)
    
    llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    result = await engine.run(
        llm=llm,
        tools=qt,
        query=query,
    )

    return result

