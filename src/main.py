import asyncio
from workflow import run_due_diligence

async def main():
   print("Running Multi-Agents")
   results = await run_due_diligence(startup_name="Vercel", 
                      startup_descrption="Deployment Made Easy")

   print("Final State: ", results.get('current_stage'))
   print("Errors: ", results.get('error', []))


if __name__ == "__main__":
    asyncio.run(main())