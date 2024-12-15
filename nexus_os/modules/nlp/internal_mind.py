import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_ollama import OllamaLLM

async def analyze_conversation(user_message, memory):
    """
    Perform internal analysis of the conversation and generate a concise thought.
    """
    system_prompt = """
    You are an AI with an internal mind capable of reflecting deeply. Generate a concise internal thought based on the user's input and memory.
    """
    context = [{"role": "system", "content": system_prompt}]
    context += [{"role": "user", "content": m} for m in memory]
    context.append({"role": "user", "content": user_message})

    # Configure the Ollama LLM
    llm = OllamaLLM(model="llama3.2:latest", max_tokens=15, host="http://localhost:11434", temperature=0.5)

    # Use ThreadPoolExecutor for blocking call in async function
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        thought = await loop.run_in_executor(executor, llm.invoke, context)

    return thought.strip()
