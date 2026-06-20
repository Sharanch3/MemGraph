from typing import Final
from backend.state import ChatState
from backend.base_model import base_model
from backend.chains import memory_extractor
from langgraph.store.base import BaseStore
from backend.tools import model_with_tools
from langchain_core.runnables import RunnableConfig
from backend.store_helper import _namespace, load_memories
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage




#Threshold that triggers summarization
MAX_HISTORY_TOKEN: Final[int] = 6000

#Token budget passed to the LLM in chat_node
RECENT_MESSAGE_TOKENS: Final[int] = 2000



#Router Function
def should_summarize(state: ChatState) ->str:
    
    """ 
    Routes to summarization when the conversation exceeds the token limit; otherwise continues normal chat flow.
    
    """
    messages = state.get("messages", "")

    kept = trim_messages(
        messages= messages,
        max_tokens= MAX_HISTORY_TOKEN,
        token_counter= count_tokens_approximately,
        strategy= "last"

    )


    return "summarize" if len(kept) < len(messages) else "chat"
    



#NODES
def summary_node(state: ChatState) ->dict:

    """ 
    Summarizes trimmed conversation history or updates 
    the running summary if it exists.
    
    """
    messages = state.get("messages", "")

    existing_summary = state.get("summary", "")

    kept = trim_messages(
        messages= messages,
        max_tokens= MAX_HISTORY_TOKEN,
        token_counter= count_tokens_approximately,
        strategy= "last"
    )

    #Extract old messages
    old_messages = messages[: len(messages) - len(kept)]

    if not old_messages:
        return {}
    

    conversation = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in old_messages
    )


    prompt = f"""
                Current Summary:

                {existing_summary}

                Extend the summary using the conversation below.

                Conversation:

                {conversation}

                Return only the updated summary.
              """
    
    response = base_model.invoke([
        HumanMessage(content= prompt)
    ])


    return {
        "summary": response.content,
        "kept_messages": kept
    }





def cleanup_node(state: ChatState) ->dict:

    """
    Remove messages that were just summarized, keeping 
    only what fits the budget.
    
    """

    messages = state.get("messages", "")

    kept = state.get("kept_messages", [])

    
    if len(messages) == len(kept):

        return {}
    

    else:
        messages_to_remove = [
            RemoveMessage(msg.id)
            for msg in messages[: len(messages) - len(kept)]
        ]


        return {
        "messages": messages_to_remove
        }
    




def memory_write_node(state: ChatState, config: RunnableConfig, *,store: BaseStore) ->dict:

    """
    Persist long-term user memories.

    Trims recent conversation history, uses an LLM to extract durable
    user facts (e.g., name, profession, goals, projects, interests,
    and preferences), and stores them in the memory store. Existing
    memories are updated only when a new value differs from the
    previously stored value.
    
    """

    recent = trim_messages(
        messages= state.get("messages", ""),
        max_tokens= 2000,
        token_counter= count_tokens_approximately,
        strategy= "last"
    )

    conversation = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in recent
        if isinstance(msg, HumanMessage)
    )

    facts = memory_extractor.invoke(
        [HumanMessage(
            content=f"""
             Extract durable user facts worth remembering across future conversations.

            Store only:
            - Name
            - Profession
            - Goals
            - Projects
            - Interests
            - Preferences

            Ignore temporary requests and one-time tasks.

            Conversation:
            {conversation}
            """
        )]
    )

    ns = _namespace(state["user_id"])


    for fact in facts.facts:
        #Skip facts missing a key or a value
        if not fact.key or not fact.value:
            continue

        #Check Existing Memory
        existing = store.get(namespace= ns, key= fact.key)

        existing_value = existing.value.get("value") if existing else None

        if existing_value != fact.value:
            store.put(
                namespace= ns,
                key= fact.key,
                value= {"value": fact.value} #must be a dict
            )
        
    
    return {}





def chat_node(state: ChatState, config: RunnableConfig, *, store: BaseStore) ->dict:

    """
    Build the prompt from:
    - System instructions
    - Long-term memory
    - Conversation summary
    - Recent messages

    Then invoke the model and append the response.
    """

    messages = state["messages"]

    summary = state.get("summary", "")

    user_id = state["user_id"]


    recent_messages = trim_messages(
        messages=messages,
        max_tokens=RECENT_MESSAGE_TOKENS,
        token_counter=count_tokens_approximately,
        strategy="last",
    )
    

    prompt = [
        SystemMessage(
            content=(
                "You are a helpful assistant. "
                "Answer clearly and concisely."
            )
        )
    ]


    # Inject long-term memory
    memory_context = load_memories(store, user_id)

    if memory_context:
        prompt.append(
            SystemMessage(content=memory_context)
        )

    # Inject conversation summary
    if summary:
        prompt.append(
            SystemMessage(
                content=f"Conversation Summary:\n\n{summary}"
            )
        )

    # Inject recent conversation
    prompt.extend(recent_messages)

    response = model_with_tools.invoke(prompt)



    return {
        "messages": [response]
    }




