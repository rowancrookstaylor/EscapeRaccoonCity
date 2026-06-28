from importlib.machinery import NamespaceLoader
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import CitizenAgent
import random
from mesa.datacollection import DataCollector


class ZombieModel(Model):
    def count_escaped(model):
        return sum(1 for a in model.schedule.agents if a.state == "R")

    def count_infected(model):
        return sum(1 for a in model.schedule.agents if a.state == "I")

    def count_dead_pre_infection(model):
        # died while never infected
        return sum(1 for a in model.schedule.agents if a.state == "D" and getattr(a, "ever_infected", False) == False)

    def count_dead_infected(model):
        return sum(1 for a in model.schedule.agents if a.state == "D" and getattr(a, "ever_infected", False) == True)

    def __init__(self, N=500, width=50, height=50):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        self.width = width
        self.height = height

        self.escaped = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Escaped": count_escaped,
                "Infected": count_infected,
                "Dead_PreInfection": count_dead_pre_infection,
                "Dead_Infected": count_dead_infected
            }
        )

        
        
        # build agents
        for i in range(self.num_agents):
            agent = CitizenAgent(i, self)
            self.schedule.add(agent)

            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(agent, (x,y))


        # initial infection
        for agent in random.sample(self.schedule.agents, int(N * .05)):
            agent.state = "I"

    

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)