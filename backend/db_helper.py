from backend.stm_graph import checkpointer
from langgraph.store.base import BaseStore


#FOR STM
def retrieve_all_threads():
    all_threads = set()

    for checkpoint in checkpointer.list(config = None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    
    return list(all_threads)




#FOR LTM
MEMORY_NAMESPACE = "user_memories" #top-level namespace in the Store


def _namespace(user_id: str) ->tuple[str, ...]:
    """Each user gets their own namespace"""

    return (MEMORY_NAMESPACE, user_id)



def load_memories(store: BaseStore, user_id: str) -> str:
    try:
        items = store.search(_namespace(user_id))
    except Exception as e:
        print(f"[load_memories] store.search failed: {e}")
        return ""

    memories = []
    for item in items:
        try:
            val = item.value.get("value", "") if isinstance(item.value, dict) else ""
            if val:
                memories.append(f"{item.key}: {val}")
        except Exception as e:
            print(f"[load_memories] Skipping corrupt item {item.key}: {e}")

    return "\n".join(memories)