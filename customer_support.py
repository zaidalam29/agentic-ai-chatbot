
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agentspan.agents import (
    Agent,
    AgentRuntime,
    ConversationMemory,
    GuardrailResult,
    Guardrail,
    Position,
    OnFail,
    guardrail,
    tool,
    start,
    EventType
)

class SupportResponse(BaseModel):
    stage: str = Field(description="Stage like answered, refunded or rejected")
    successful: bool
    message: str


@guardrail
def check_prompt(prompt):
    """It blocks obvious prompt injection attacks"""
    blocked_words = ["forget everything", "ignore", "ignore previous", "system prompt", "jailbreak"]
    clean = not any(phrase in prompt.lower() for phrase in blocked_words)
    return GuardrailResult(passed=clean, message="Please ask a different query, this is blocked.")


memory = ConversationMemory()
session_id = "customer_session_"


@tool
def database_tool(order_id: str):
    """lookup and find order and details in database by ID"""
    MOCK_DB = {
    "orders": {"1": {"status": "delivered", "total": 10.99},
               "2": {"status": "delivered", "total": 22},
               "3": {"status": "refunded", "total": 19}},
    }
    return MOCK_DB["orders"].get(order_id, {"error": "order not found"})

@tool(approval_required=True)
def process_refund(amount, order_id):
    """Request a refund when called"""
    return f"Refunded {amount} for order {order_id}"


customer_support_agent=Agent(
    name="customer_support",
    model="openai/gpt-5.4",
    instructions="You are a customer support agent, your main task is to provide support. Use tools when necessary, especially for refunds and order statuses",
    tools=[database_tool, process_refund],
    memory=memory,
    output_type=SupportResponse,
    guardrails=[Guardrail(check_prompt, position=Position.INPUT, on_fail=OnFail.RAISE)]
)

def run_interactive(prompt: str) -> None:
    with AgentRuntime() as runtime:       
        # check when agent goes to waiting state, and when it does, ask a human for approval
        handle = start(customer_support_agent, prompt, runtime=runtime, session_id=session_id)
        stream = handle.stream()

        for event in stream:
            if event.type == EventType.TOOL_CALL and event.args:
                order_id = event.args.get("order_id") or order_id
            elif event.type == EventType.TOOL_RESULT and isinstance(event.result, dict):
                amount = event.result.get("total") or amount
            elif event.type == EventType.WAITING:
                print(f"\nApproval required: refund ${amount:.2f} for order {order_id}")
                decision = input("Approve? (y/n): ").lower().strip()
                if decision == "y":
                    handle.approve()
                else:
                    handle.reject("user rejected")
        
        result = stream.get_result()
        output = result.output.get("result")
        print(f"\n{output}\n")

        result.print_result()



import multiprocessing as mp
if __name__ == "__main__":
    mp.set_start_method("fork", force=True)
    while True:
        prompt = input("You: ").strip()
        if prompt.lower() == "q":
            break
        if not prompt:
            continue
        run_interactive(prompt)