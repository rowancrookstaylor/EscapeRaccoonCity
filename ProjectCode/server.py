
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import TextElement
from model import ZombieModel


class SimulationStats(TextElement):
    def render(self, model):
        days_elapsed = (model.time / model.max_time) * 9

        survivors = sum(1 for agent in model.schedule.agents if hasattr(agent, "state") and agent.state == "S")

        exposed = sum(1 for agent in model.schedule.agents if hasattr(agent, "state") and agent.state == "E")

        infected = sum(1 for agent in model.schedule.agents if hasattr(agent, "state") and agent.state == "I")
        dead = sum(1 for agent in model.schedule.agents if hasattr(agent, "state") and agent.state == "D")
        
        escaped = sum(1 for agent in model.schedule.agents if hasattr(agent, "state") and agent.state == "R")

        dead_infected = sum(1 for agent in model.schedule.agents if hasattr(agent, "state") and agent.state == "D" and agent.ever_infected == True)

        total = survivors + exposed + infected + dead + escaped
        percentage_infected = (infected / total) * 100 if total > 0 else 0
        percentage_total_escaped = (escaped / total) * 100 if total > 0 else 0
        percentage_still_alive = ((survivors) / total) * 100 if total > 0 else 0
        percentage_dead_before_infection = ((dead-dead_infected) / total) * 100 if total > 0 else 0
        percentage_dead_after_infection = (dead_infected / total) * 100 if total > 0 else 0

        return f" Day: {round(days_elapsed,2)} / 9<br/> Survivors: {round(survivors, 2)} | Exposed: {round(exposed, 2)} | Infected: {round(infected, 2)} | Dead: {round(dead, 2)} | Escaped: {round(escaped, 2)} <br/> Percentage Infected: {round(percentage_infected, 2)} <br/>Percentage Escaped: {round(percentage_total_escaped, 2)} <br/>Percentage Alive and in the City: {round(percentage_still_alive, 2)} <br/>Percentage Dead Before Infection: {round(percentage_dead_before_infection,2)} | Percentage Dead After Infection: {round(percentage_dead_after_infection,2)}"

def agent_portrayal(agent):
    if hasattr(agent, "state") and agent.state == "S":
        color = "green"
    elif hasattr(agent, "state") and agent.state == "E":
        color = "orange"
    elif hasattr(agent, "state") and agent.state == "I":
        color = "red"
    elif hasattr(agent, "state") and agent.state == "D":
        color = "black"
    elif hasattr(agent, "state") and agent.state == "R":
        color = "gray"

    if hasattr(agent, "state"):
        return {
        "Shape": "circle",
        "Color": color,
        "Filled": "true",
        "r": .5,
        "Layer": 0
        }

    if hasattr(agent, "obstacle") and agent.obstacle:
        return {
            "Shape": "rect",
            "Color": "gray",
            "Filled": "true",
            "w": 1,
            "h": 1,
            "Layer": 0
        }
    if agent.__class__.__name__ == "SupplyDepot":
        color = "blue"
        shape = "rect"
        return {
            "Shape": shape,
            "Color": color,
            "Filled": "true",
            "w": .8,
            "h": .8,
            "Layer": 0
        }


    


    

stats = SimulationStats()

grid = CanvasGrid(agent_portrayal, 100, 100, 600, 600)

server = ModularServer(
    ZombieModel,
    [stats, grid],
    "Raccoon City Outbreak",
    {}
)

