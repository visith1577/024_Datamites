from workflows.workflow_init import rag_main
import asyncio

output = asyncio.run(rag_main(
        query="Provide a brief summary of the presidential elections"
    )
)

print(output)