import asyncio
from app.services.llm_service import llm_service

async def main():
    try:
        print("Starting stream...")
        async for token in llm_service.stream("Say hello world"):
            print(f"TOKEN: {repr(token)}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
