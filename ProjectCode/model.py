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
            # larger central blocks
            (20,20,6,8),
            (32,22,7,6),
            (48,15,8,7),
            (62,20,6,9),
            (75,18,8,6),

            # upper city
            (10,8,5,6),
            (25,5,7,5),
            (40,8,6,6),
            (55,5,5,7),
            (85,8,6,5),

            # middle city
            (5,35,7,8),
            (18,42,6,5),
            (30,35,8,7),
            (45,40,5,8),
            (58,32,7,6),
            (72,38,8,7),
            (88,45,5,8),

            # lower city
            (8,65,8,6),
            (22,72,6,8),
            (35,62,7,5),
            (50,70,8,7),
            (65,65,6,8),
            (80,72,7,6),

            # bottom city
            (12,85,6,5),
            (30,88,8,6),
            (48,82,6,7),
            (65,88,7,5),
            (82,85,8,6),
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

        self.time = 0
        self.max_time = 30
        self.city_destroyed = False

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
                "Day": lambda m: (m.time / m.max_time) * 9,

                "Escaped": self.count_escaped,
                "Survivors": self.count_survivors,
                "Exposed": self.count_exposed,
                "Infected": self.count_infected,

                "Dead": lambda m: sum(
                    1 for a in m.schedule.agents 
                    if hasattr(a,"state") and a.state == "D"),

                "Dead_PreInfection": self.count_dead_pre_infection,
                "Dead_Infected": self.count_dead_infected,

                "Percent_Infected": lambda m:
                    (self.count_infected() /
                     max(1,m.num_agents)) * 100,

                "Percent_Escaped": lambda m:
                    (self.count_escaped() /
                     max(1,m.num_agents)) * 100,

                "Percent_Alive_In_City": lambda m:
                    (self.count_survivors() /
                     max(1,m.num_agents)) * 100,

                "Food_Remaining": lambda m:
                    sum(
                        d.food for d in m.schedule.agents
                        if isinstance(d, SupplyDepot)
                    ),

                "Water_Remaining": lambda m:
                    sum(
                        d.water for d in m.schedule.agents
                        if isinstance(d, SupplyDepot)
                    ),

                "Weapons_Remaining": lambda m:
                    sum(
                        d.weapons for d in m.schedule.agents
                        if isinstance(d, SupplyDepot)
                    )
            }
        )

        
        
        # build agents
        for i in range(self.num_agents):
            agent = CitizenAgent(i, self)
            self.schedule.add(agent)

            while True:
                pos = (random.randrange(self.width),random.randrange(self.height))

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
                pos = (random.randrange(self.width), random.randrange(self.height))

                if self.valid_position(pos):
                    break

            self.grid.place_agent(depot, pos)

    
    def destroy_city(self):
        self.city_destroyed = True
        for agent in self.schedule.agents:

            if hasattr(agent, "state"):

                # escaped citizens survive
                if agent.state != "R":
                    agent.state = "D"
                    agent.obstacle = False
                    agent.current_path = []


    def generate_results(self):

        import matplotlib.pyplot as plt

        data = self.datacollector.get_model_vars_dataframe()

        plt.figure(figsize=(10,5))

        plt.plot(
            data["Day"],
            data["Survivors"],
            label="Survivors")

        plt.plot(
            data["Day"],
            data["Infected"],
            label="Infected")

        plt.plot(
            data["Day"],
            data["Escaped"],
            label="Escaped")

        plt.plot(
            data["Day"],
            data["Dead"],
            label="Dead")

        plt.xlabel("Days")
        plt.ylabel("Citizens")
        plt.title("Raccoon City Outbreak Simulation")

        plt.legend()

        plt.savefig("simulation_results.png")

        plt.show()



    def step(self):
        if self.city_destroyed:
            return

        self.time += 1
        self.schedule.step()
        if self.time >= self.max_time:
            self.datacollector.collect(self)
            self.generate_results()

            print("\n--- MISSILE STRIKE ---")
            print("Final statistics before destruction:")
            print(self.datacollector.get_model_vars_dataframe().tail())

            self.destroy_city()

            return
        self.datacollector.collect(self)
