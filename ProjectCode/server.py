
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from networkx import modularity_matrix
from model import ZombieModel

def agent_portrayal(agent):
    if agent.state == "S":
        color = "green"
    elif agent.state == "E":
        color = "yellow"
    elif agent.state == "I":
        color = "red"
    else:
        color = "black"


    return {
        "Shape": "circle",
        "Color": color,
        "Filled": "true",
        "r": .5,
        "Layer": 0
        }

grid = CanvasGrid(agent_portrayal, 50, 50, 600, 600)

server = ModularServer(
    ZombieModel,
    [grid],
    "Raccoon City Outbreak",
    {"N": 500, "width": 50, "height": 50})