from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from workflows.workflow_init import rag_main, main
from contextlib import asynccontextmanager
from llama_index.core.llms import ChatResponse
from pydantic import BaseModel
import asyncio
from workflows.workflow_rag import prepare_query_engine

qt = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize qt once and store it
    global qt
    qt = prepare_query_engine("documents")
    yield

app = FastAPI(
    lifespan=lifespan
)



origins = [
    'http://localhost:3000'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

class JsonOutput(BaseModel):
    output: str


@app.get("/rag", response_model=JsonOutput)
def get_rag_output(
    input: str = Query(..., title="Input values", description="Input values for RAG model")
):
    output = asyncio.run(rag_main(query=input, qt=qt))

    return JsonOutput(output=output)  



@app.get("/search", response_model=JsonOutput)
def search(
    input: str = Query(..., title="Query string", description="Query string to search")
):
    output: ChatResponse = asyncio.run(main(query=input))
    
    return JsonOutput(output=output.message.content)
