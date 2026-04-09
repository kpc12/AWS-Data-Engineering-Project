import json

def read_config(path):
    """Read configuration from a JSON file."""
    with open(path, 'r') as file:
        config = json.load(file)
    return config
