import os

from meibel import MeibelClient

client = MeibelClient(
    api_key=os.environ["MEIBEL_API_KEY"],
)

for agent in client.agents.list():
    print(agent)
