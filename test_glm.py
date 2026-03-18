import asyncio
import time
from app.agent.clients import glm_client, GLM_MODEL

async def test_glm():
    print(f"Testing model: {GLM_MODEL}")
    prompt = "Hello, can you write a short poem about coding? I want to test your response speed."
    print(f"Prompt: {prompt}")
    
    start_time = time.time()
    
    try:
        response = await glm_client.chat.completions.create(
            model=GLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        end_time = time.time()
        
        print("\nResponse received:")
        print(response.choices[0].message.content)
        print(f"\nTime taken: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error calling GLM: {e}")

if __name__ == "__main__":
    asyncio.run(test_glm())
