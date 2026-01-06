from client_session import client
import os
import logging

# Logging setup
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

# Load Plugins logic
def load_plugins():
    plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')
    if not os.path.exists(plugin_path):
        os.makedirs(plugin_path)
        
    for file in os.listdir(plugin_path):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = f"plugins.{file[:-3]}"
            try:
                __import__(module_name)
                print(f"Loaded plugin: {module_name}")
            except Exception as e:
                print(f"Failed to load {module_name}: {e}")

# Start
print("Bot is starting...")
load_plugins() 

if __name__ == '__main__':
    try:
        client.run_until_disconnected()
    except Exception as e:
        print(f"Error: {e}")
