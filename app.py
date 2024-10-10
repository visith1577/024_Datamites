from fastapi import FastAPI, Query
from workflows.workflow_init import rag_main, main
from typing import List

app = FastAPI()

@app.get("/rag/")
def get_rag_output(
    input: str = Query(..., title="Input values", description="Input values for RAG model")
):
    output = rag_main(input)
    return {"output": output}  



@app.get("/search/")
def search(
    query: str = Query(None, title="Query string", description="Query string to search")
):
    output = main(query)
    return {"query": output}
