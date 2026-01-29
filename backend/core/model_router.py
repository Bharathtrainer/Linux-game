def select_model(level: str):
    if level in ["entry", "operator"]:
        return "llama-3.1-nemotron-nano-8b-v1"
    elif level in ["engineer", "sre"]:
        return "llama-3.3-nemotron-super-49b-v1.5"
    elif level == "expert":
        return "llama-3.1-nemotron-ultra-253b-v1"
    else:
        raise ValueError("Unknown level")
