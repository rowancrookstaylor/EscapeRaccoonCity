
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import TextElement
from model import ZombieModel


class SimulationStats(TextElement):
    def render(self, model):
        survivors = sum(1 for agent in model.schedule.agents if agent.state == "S")

        exposed = sum(1 for agent in model.schedule.agents if agent.state == "E")

        infected = sum(1 for agent in model.schedule.agents if agent.state == "I")

        dead = sum(1 for agent in model.schedule.agents if agent.state == "D")
        
        escaped = sum(1 for agent in model.schedule.agents if agent.state == "R")
        
        return f"Survivors: {survivors} | Exposed: {exposed} | Infected: {infected} | Dead: {dead} | Escaped: {escaped}"

def agent_portrayal(agent):
    if agent.state == "S":
        color = "green"
    elif agent.state == "E":
        color = "yellow"
    elif agent.state == "I":
        color = "red"
    elif agent.state == "D":
        color = "black"
    else:
        color = "gray"


    return {
        "Shape": "circle",
        "Color": color,
        "Filled": "true",
        "r": .5,
        "Layer": 0
        }

stats = SimulationStats()

grid = CanvasGrid(agent_portrayal, 50, 50, 600, 600)

server = ModularServer(
    ZombieModel,
    [stats, grid],
    "Raccoon City Outbreak",
    {"N": 500, "width": 50, "height": 50})

