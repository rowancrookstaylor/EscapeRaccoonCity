from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import CitizenAgent
import random
from mesa.datacollection import DataCollector
from obstacle import ObstacleAgent
from supply_depo import SupplyDepot


class ZombieModel(Model):
    def count_escaped(model):
        return sum(1 for a in model.schedule.agents if hasattr(a, "state") and  a.state == "R")

    def count_infected(model):
        return sum(1 for a in model.schedule.agents if hasattr(a, "state") and  a.state == "I")

    def count_dead_pre_infection(model):
        # died while never infected
        return sum(1 for a in model.schedule.agents if hasattr(a, "state") and  a.state == "D" and getattr(a, "ever_infected", False) == False)

    def count_dead_infected(model):
        return sum(1 for a in model.schedule.agents if hasattr(a, "state") and a.state == "D" and getattr(a, "ever_infected", False) == True)

    def count_survivors(model):
        return sum(1 for a in model.schedule.agents if hasattr(a, "state") and a.state == "S")

    def count_exposed(model):
        return sum(1 for a in model.schedule.agents if hasattr(a, "state") and  a.state == "E")


    def create_obstacles(self):
        obstacle_id = 10000

        buildings = [
            (20,20,10,15),
            (50,10,15,10),
            (70,50,10,20),
            (30,70,20,10),
            (5,10,6,8),
            (15,45,8,6),
            (5,70,10,10),
            (35,10,7,5),
            (42,30,8,8),
            (55,35,6,10),
            (80,15,8,8),
            (88,35,6,12),
            (75,80,12,7),
        ]

        for x_start, y_start, width, height in buildings:

            for x in range(x_start, x_start + width):
                for y in range(y_start, y_start + height):

                    obstacle = ObstacleAgent(
                        obstacle_id,
                        self
                    )

                    self.grid.place_agent(
                        obstacle,
                        (x,y)
                    )

                    obstacle_id += 1


    def valid_position(self,pos):
        agents = self.grid.get_cell_list_contents([pos])

        for agent in agents:
            if hasattr(agent,"obstacle") and agent.obstacle:
                return False

        return True


    def __init__(self, N=500, width=100, height=100):
        self.num_agents = N
        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)

        self.width = width
        self.height = height

        self.create_obstacles()

        self.escaped = 0

        self.exits = []

        for x in range(self.width):
            self.exits.append((x,0))
            self.exits.append((x,self.height-1))

        for y in range(self.height):
            self.exits.append((0,y))
            self.exits.append((self.width-1,y))

        self.datacollector = DataCollector(
            model_reporters={
                "Escaped": self.count_escaped,
                "Infected": self.count_infected,
                "Dead_PreInfection": self.count_dead_pre_infection,
                "Dead_Infected": self.count_dead_infected,
                "Survivors": self.count_survivors,
                "Exposed": self.count_exposed
            }
        )

        
        
        # build agents
        for i in range(self.num_agents):
            agent = CitizenAgent(i, self)
            self.schedule.add(agent)

            while True:
                pos = (
                    random.randrange(self.width),
                    random.randrange(self.height)
                )

                if self.valid_position(pos):
                    break

            self.grid.place_agent(agent, pos)


        # initial infection
        for agent in random.sample(self.schedule.agents, int(N * .3)):
            agent.state = "I"
            agent.home_pos = agent.pos



        for i in range(5):
            depot = SupplyDepot(1000+i, self)
            self.schedule.add(depot)

            while True:
                pos = (
                    random.randrange(self.width),
                    random.randrange(self.height)
                )

                if self.valid_position(pos):
                    break

            self.grid.place_agent(depot, pos)

    

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)