from importlib.machinery import NamespaceLoader
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import CitizenAgent
import random


class ZombieModel(Model):
    def __init__(self, N=500, width=50, height=50):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        self.width = width
        self.height = height

        self.escaped = 0
        
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