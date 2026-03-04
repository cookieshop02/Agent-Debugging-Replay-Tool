"""
groq_agent.py
─────────────
A REAL agent using Groq API + tracer recording every step.

Setup:
  1. pip install groq
  2. Get free API key from console.groq.com
  3. Replace "your-groq-api-key" below with your actual key
  4. Run: python groq_agent.py
  5. Then: streamlit run app.py  (to see the recording)
"""

import sys
import os
import time

# ── point Python to our tracer folder ──────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tracer"))
from tracer.recorder import AgentTracer

# ── Groq client setup ──────────────────────────
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))   # 🔑 replace this

TRACER_API_KEY = os.getenv("TRACER_API_KEY")   # 🔑 your Agent Tracer key (from /register)

MODEL = "llama-3.1-8b-instant"   # fast + free on Groq


# ─────────────────────────────────────────────
# TOOLS (simple Python functions)
# These are the tools our agent can "use"
# ─────────────────────────────────────────────

def calculator(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        # only allow safe math characters
        allowed = set("0123456789+-*/(). ")
        if all(c in allowed for c in expression):
            result = eval(expression)
            return str(result)
        return "Error: unsafe expression"
    except Exception as e:
        return f"Error: {e}"


def word_counter(text: str) -> str:
    """Count words in a given text."""
    words = len(text.strip().split())
    chars = len(text)
    return f"{words} words, {chars} characters"


def reverse_text(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


# Map tool name (string) → actual function
TOOLS = {
    "calculator": calculator,
    "word_counter": word_counter,
    "reverse_text": reverse_text,
}


# ─────────────────────────────────────────────
# HELPER: call Groq LLM
# ─────────────────────────────────────────────

def call_llm(messages: list) -> tuple[str, int]:
    """
    Send messages to Groq and get back (response_text, tokens_used).
    We return tokens so the tracer can record the cost.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=500,
    )
    text   = response.choices[0].message.content
    tokens = response.usage.total_tokens
    return text, tokens


# ─────────────────────────────────────────────
# HELPER: parse tool call from LLM response
# ─────────────────────────────────────────────

def parse_tool_call(response: str):
    """
    We ask the LLM to respond in this exact format when it wants to use a tool:
        TOOL: tool_name
        INPUT: the input

    This function parses that format.
    Returns (tool_name, tool_input) or (None, None) if no tool call found.
    """
    lines = response.strip().split("\n")
    tool_name  = None
    tool_input = None

    for line in lines:
        if line.startswith("TOOL:"):
            tool_name = line.replace("TOOL:", "").strip()
        if line.startswith("INPUT:"):
            tool_input = line.replace("INPUT:", "").strip()

    if tool_name and tool_input:
        return tool_name, tool_input
    return None, None


# ─────────────────────────────────────────────
# THE AGENT LOOP
# ─────────────────────────────────────────────

def run_agent(user_task: str):
    """
    Run a simple ReAct-style agent:
      Think → Act (tool) → Observe → Think → Act → ... → Answer

    Every step is recorded by the tracer.
    """

    print(f"\n{'='*55}")
    print(f"Task: {user_task}")
    print(f"{'='*55}\n")

    # ── start recording ────────────────────────
    tracer = AgentTracer(api_key=TRACER_API_KEY, name=f"Groq Agent: {user_task[:40]}")
    tracer.start()

    # ── system prompt ──────────────────────────
    # We tell the LLM exactly how to use tools
    system_prompt = """You are a helpful assistant that can use tools to answer questions.

Available tools:
- calculator: evaluates math expressions. Example: 2 + 2 * 10
- word_counter: counts words in text. Example: Hello world
- reverse_text: reverses a string. Example: Hello

When you need to use a tool, respond EXACTLY in this format (nothing else):
TOOL: tool_name
INPUT: the input for the tool

When you have the final answer and don't need any more tools, respond EXACTLY:
ANSWER: your final answer here

Always use a tool first if the task requires calculation, counting, or reversing.
Never guess — always use the tool."""

    # ── conversation history ───────────────────
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_task}
    ]

    max_steps = 5   # prevent infinite loops
    step = 0

    while step < max_steps:
        step += 1
        print(f"--- Step {step} ---")

        # ── call LLM ──────────────────────────
        start_time = time.time()
        try:
            llm_response, tokens = call_llm(messages)
            duration_ms = (time.time() - start_time) * 1000
        except Exception as e:
            tracer.record_error(f"LLM call at step {step}", e)
            tracer.finish(status="error")
            print(f"LLM call failed: {e}")
            return

        print(f"LLM said: {llm_response[:120]}...")

        # ── record the LLM call ────────────────
        tracer.record_llm(
            prompt=messages[-1]["content"],   # last user message
            response=llm_response,
            tokens=tokens
        )

        # add LLM response to conversation history
        messages.append({"role": "assistant", "content": llm_response})

        # ── check if LLM wants to use a tool ──
        tool_name, tool_input = parse_tool_call(llm_response)

        if tool_name:
            # LLM wants to call a tool
            print(f"Using tool: {tool_name}({tool_input})")

            if tool_name not in TOOLS:
                # tool doesn't exist — record error
                error_msg = f"Tool '{tool_name}' does not exist. Available: {list(TOOLS.keys())}"
                tracer.record_error(f"Tool call: {tool_name}", Exception(error_msg))

                # tell LLM about the error so it can recover
                messages.append({
                    "role": "user",
                    "content": f"ERROR: {error_msg}"
                })
                continue

            # run the real tool
            tool_start = time.time()
            try:
                tool_result = TOOLS[tool_name](tool_input)
                tool_ms = (time.time() - tool_start) * 1000
            except Exception as e:
                tracer.record_error(f"Tool '{tool_name}' crashed", e)
                messages.append({"role": "user", "content": f"ERROR: tool crashed: {e}"})
                continue

            print(f"Tool result: {tool_result}")

            # ── record the tool call ───────────
            tracer.record_tool(
                tool_name=tool_name,
                input_data=tool_input,
                output_data=tool_result,
                duration_ms=tool_ms
            )

            # give the tool result back to the LLM
            messages.append({
                "role": "user",
                "content": f"Tool result: {tool_result}\n\nNow give me the ANSWER."
            })

        elif "ANSWER:" in llm_response:
            # LLM has the final answer — we're done!
            final_answer = llm_response.split("ANSWER:")[-1].strip()
            print(f"\n✅ Final Answer: {final_answer}")
            tracer.finish(status="success")
            print(f"\n📊 Session saved. Open dashboard to inspect: streamlit run app.py")
            return final_answer

        else:
            # LLM responded with something unexpected
            # nudge it back on track
            messages.append({
                "role": "user",
                "content": "Please respond using either TOOL/INPUT format or ANSWER format."
            })

    # hit max steps without finishing
    tracer.record_error("Agent loop", Exception(f"Hit max steps ({max_steps}) without an answer"))
    tracer.finish(status="error")
    print("❌ Agent hit max steps limit")


# ─────────────────────────────────────────────
# RUN SOME TASKS
# ─────────────────────────────────────────────

if __name__ == "__main__":

    # Task 1 — needs calculator tool
    run_agent("What is 847 multiplied by 36, then add 512?")

    print("\n" + "="*55 + "\n")

    # Task 2 — needs word counter tool
    run_agent("How many words are in this sentence: The quick brown fox jumps over the lazy dog")

    print("\n" + "="*55 + "\n")

    # Task 3 — needs reverse tool
    run_agent("What is 'hello world' spelled backwards?")

    print("\n")
    print("All tasks done! Now run:  streamlit run app.py")
