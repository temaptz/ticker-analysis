from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
import operator
from typing import Annotated, List, Tuple, Union
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from lib.agent import utils

class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
                    "If you need to further use tools to get the answer, use Plan."
    )

class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

tools = [TavilySearchResults(max_results=3, tavily_api_key='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')]
llm = ChatOllama(model='PetrosStav/gemma3-tools:4b', verbose=True).bind_tools(tools=tools)
prompt = 'Ты полезный ИИ ассистент помощник. Отвечай на Русском языке.'
agent_executor = create_react_agent(llm, tools, prompt=prompt, debug=True)
planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.""",
        ),
        ("placeholder", "{messages}"),
    ]
)
replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)
planner = planner_prompt | llm.with_structured_output(Plan)
replanner = replanner_prompt | llm.with_structured_output(Act)


def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = agent_executor.invoke({"messages": [("user", task_formatted)]})

    return {'past_steps': [(task, agent_response["messages"][-1].content)]}


def plan_step(state: PlanExecute):
    print('WILL PLAN')
    print(state)
    plan = planner.invoke({'messages': [('user', state['input'])]})
    return {'plan': plan.steps}


def replan_step(state: PlanExecute):
    output = replanner.invoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}


def should_end(state: PlanExecute):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"

def run():
    workflow = StateGraph(PlanExecute)

    # Add the plan node
    workflow.add_node("planner", plan_step)

    # Add the execution step
    workflow.add_node("agent", execute_step)

    # Add a replan node
    workflow.add_node("replan", replan_step)

    workflow.add_edge(START, "planner")

    # From plan we go to agent
    workflow.add_edge("planner", "agent")

    # From agent, we replan
    workflow.add_edge("agent", "replan")

    workflow.add_conditional_edges(
        "replan",
        # Next, we pass in the function that will determine which node is called next.
        should_end,
        ["agent", END],
    )

    # Finally, we compile it!
    # This compiles it into a LangChain Runnable,
    # meaning you can use it as you would any other runnable
    app = workflow.compile(debug=True)

    # utils.draw_graph(app)

    response = app.invoke({'input': 'Кто победитель чемпионата россии по футболу в 2024'})

    print('RESPONSE', response)
    print('FINAL RESULT', response['messages'][-1].content)