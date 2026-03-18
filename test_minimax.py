import asyncio
import time
from app.agent.clients import minimax_client, MINIMAX_MODEL

async def test_minimax():
    print(f"Testing model: {MINIMAX_MODEL}")
    prompt = "Hello, can you write a short poem about coding? I want to test your response speed."
    print(f"Prompt: {prompt}")
    
    start_time = time.time()
    
    try:
        response = await minimax_client.chat.completions.create(
            model="minimax/minimax-m2.5:free",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        
        end_time = time.time()
        
        print("\nResponse received:")
        print(response.choices[0].message.content)
        print(f"\nTime taken: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error calling Minimax: {e}")

if __name__ == "__main__":
    asyncio.run(test_minimax())
