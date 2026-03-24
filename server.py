"""
Parlant server - sets up agent and guidelines, then starts HTTP server.
Run this first, then run interactive_agent.py in another terminal.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load .env BEFORE importing parlant
load_dotenv()

import parlant.sdk as p
from parlant.sdk import start_parlant, StartupParameters


async def setup_agent(container):
    """Create agent and guidelines using the container."""
    from parlant.core.agents import AgentStore
    from parlant.core.guidelines import GuidelineStore
    
    agent_store = container[AgentStore]
    guideline_store = container[GuidelineStore]
    
    # Create agent
    agent = await agent_store.create_agent(
        name="Shop Assistant",
        description="A helpful assistant for an online electronics store",
    )
    print(f"Created agent: {agent.name} (ID: {agent.id})")
    
    # Create guidelines
    await guideline_store.create_guideline(
        condition="customer is new to the store",
        action="give a warm welcome, explain store policies, and offer a 10% first-time discount",
    )
    
    await guideline_store.create_guideline(
        condition="customer asks about price, discount, or promotion",
        action="explain current promotions and highlight value propositions",
    )
    
    await guideline_store.create_guideline(
        condition="customer asks for technical help or troubleshooting",
        action="provide step-by-step troubleshooting guidance",
    )
    
    await guideline_store.create_guideline(
        condition="customer asks something not covered by other guidelines",
        action="be helpful, ask clarifying questions, and direct them to appropriate resources",
    )
    
    print("Created 4 guidelines")
    return agent


async def main():
    """Start server with setup, then serve HTTP."""
    params = StartupParameters(
        host="0.0.0.0",
        port=8800,
        nlp_service="openai",
        log_level="info",
        modules=[],
        migrate=False,
    )
    
    print("Starting Parlant server...")
    
    # The context manager yields container for setup, then runs serve_app after
    async with start_parlant(params) as container:
        # Setup phase - create agent and guidelines
        agent = await setup_agent(container)
        print(f"\nSetup complete. Starting HTTP server on port 8800...")
        print(f"Agent ID: {agent.id}")
        print("Run: python interactive_agent.py")
        print("Press Ctrl+C to stop\n")
        
        # DON'T block here - let the context manager exit so serve_app runs
        # serve_app() runs AFTER this block and blocks until Ctrl+C
    
    # This line is never reached until server shuts down
    print("Server shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
