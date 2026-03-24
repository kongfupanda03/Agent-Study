"""
Parlant interactive client - uses the official ParlantClient.
Run server.py first, then run this script to chat.
"""
import asyncio
import os
from dotenv import load_dotenv
from parlant.client import ParlantClient
from parlant.client.types import Participant

load_dotenv()

SERVER_URL = "http://localhost:8800"


def sync_input(prompt: str) -> str:
    """Synchronous input for use with run_in_executor."""
    return input(prompt)


async def async_input(prompt: str) -> str:
    """Async wrapper for input() that doesn't block the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_input, prompt)


async def wait_for_server(client: ParlantClient, timeout: int = 60) -> bool:
    """Wait until server is ready."""
    print("Waiting for server", end="", flush=True)
    for _ in range(timeout):
        try:
            client.health_check_healthz_get()
            print(" Ready!\n")
            return True
        except Exception:
            print(".", end="", flush=True)
            await asyncio.sleep(1)
    print(" Timeout!")
    return False


async def main():
    client = ParlantClient(base_url=SERVER_URL)
    
    # Wait for server
    if not await wait_for_server(client):
        print("Server not available. Run: python server.py")
        return
    
    # List agents and use the first one
    agents = client.agents.list()
    if not agents:
        print("No agents found. Make sure server.py is running.")
        return
    
    agent = agents[0]
    print(f"Connected to agent: {agent.name}")
    
    # Create a customer
    customer = client.customers.create(name="Test Customer")
    print(f"Customer: {customer.name} (ID: {customer.id})")
    
    # Create a session
    session = client.sessions.create(
        agent_id=agent.id,
        customer_id=customer.id,
        title="Support Session",
        allow_greeting=True,
    )
    print(f"Session: {session.id}")
    
    # Get initial events to track any greeting already sent
    initial_events = client.sessions.list_events(session_id=session.id)
    seen_message_ids = {
        e.id for e in initial_events
        if e.source == "ai_agent" and e.kind == "message"
    }
    
    print("="*50)
    print("Chat with your Parlant Agent (type 'quit' to exit)")
    print("="*50 + "\n")
    
    while True:
        user_input = (await async_input("You: ")).strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            # Send message via client
            client.sessions.create_event(
                session_id=session.id,
                kind="message",
                source="customer",
                message=user_input,
                participant=Participant(display_name="Customer"),
            )
            
            # Poll for NEW agent response (not seen before)
            print("Agent: ", end="", flush=True)
            response_printed = False
            for _ in range(60):
                await asyncio.sleep(1)
                events = client.sessions.list_events(session_id=session.id)
                
                # Find ai_agent messages we haven't seen yet
                for event in events:
                    if event.source == "ai_agent" and event.kind == "message":
                        if event.id not in seen_message_ids:
                            seen_message_ids.add(event.id)
                            if event.data and "message" in event.data:
                                print(event.data["message"])
                                response_printed = True
                                break
                if response_printed:
                    break
            else:
                print("[No response received]")
                
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
