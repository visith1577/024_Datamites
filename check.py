from workflows.workflow_init import rag_main
import asyncio


if __name__ == "__main__":
    try:
        while True:
            query = input("Enter your query: ")
            output = asyncio.run(rag_main(query=query))
            print(output)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")