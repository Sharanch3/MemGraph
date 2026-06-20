from typing import Final
from langgraph.store.base import BaseStore



#FOR LTM
MEMORY_NAMESPACE: Final[str] = "user_memories" #Top-level namespace



def _namespace(user_id: str) ->tuple[str, ...]:
    """Each user gets their own namespace"""

    return (MEMORY_NAMESPACE, user_id)




def load_memories(store: BaseStore, user_id: str) -> str:
    try:
        # searches all memories belonging to this namespace.
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