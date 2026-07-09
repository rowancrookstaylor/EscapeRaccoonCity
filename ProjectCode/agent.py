from mesa import Agent
import random
import math




class CitizenAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)

        # infection state (healthy = s, exposed = e, infected = i, dead = d, escaped = r)
        self.state = "S"
        self.infection_timer = 0
        self.ever_infected = False

        self.hunger = random.uniform(0,1)   # needs
        self.thirst = random.uniform(0,1)

        self.speed = 1  # movement
      
        self.home_pos = None    # home position (for infected)

        self.vision_radius = 10 # vision radius for infected to detect survivors

    def distance_to_edge(self, pos):
        x, y = pos
        center_x = self.model.width / 2
        center_y = self.model.height / 2
        return math.sqrt((x - center_x)**2 + (y - center_y)**2)

    def distance_to(self, pos):
        x1, y1 = self.pos
        x2, y2 = pos
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def distance_between(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

# MOVEMENT FOR THE SURVIVORS
    # movement function for survivors
    def survivor_move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)

        best_cell = None
        best_score = float("-inf")

        for cell in neighbors:
            dist = self.distance_to_edge(cell)
            score = dist + random.random()

            if score > best_score:
                best_score = score
                best_cell = cell

        if best_cell:
            self.model.grid.move_agent(self, best_cell)

# MOVEMENT FOR THE INFECTED
    # helper functions for infected movement
    def distance_from_home(self,pos):
        x1, y1 = pos
        x2, y2 = self.home_pos
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)


    # search for survivors within vision radius
    def find_nearby_survivors(self):
        nearby_survivors = []

        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False,
                                                 radius=self.vision_radius)

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])

            for agent in agents:
                if agent.state in ["S", "E"]:
                    nearby_survivors.append(agent)
        
        return nearby_survivors

    # choose priority for survivor (prioritize survivors closer to center for interception)
    def survivor_priority(self, survivor):
        distance_from_center = self.distance_to_edge(survivor.pos)

        zombie_distance = self.distance_to(survivor.pos)

        return (-distance_from_center * 2 - zombie_distance)



    # movement function
    def infected_move(self):

        survivors = self.find_nearby_survivors()

        # if there are survivors nearby, move towards the closest one
        if survivors:
            target = max(survivors, key=lambda agent: self.survivor_priority(agent))

            neighbors = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)

            best_cell = None
            best_distance = float("inf")

            for cell in neighbors:
                distance = self.distance_to(cell)

                if distance < best_distance:
                    best_distance = distance
                    best_cell = cell

            if best_cell:
                self.model.grid.move_agent(self, best_cell)

            return

        # no survivor nearby
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)

        if random.random() < .5:
            return  # stay in place; move around every other turn when idle

        valid_cells = []

        for cell in neighbors:
            distance = self.distance_from_home(cell)

            if distance <= 6:
                valid_cells.append(cell)

        if valid_cells:
            self.model.grid.move_agent(self, random.choice(valid_cells))

    def move(self):
        if self.state == "I":
            self.infected_move()
        elif self.state in ["S", "E"]:
            self.survivor_move()


    # spread infection (if infected)
    def infect_other(self):
        if self.state != "I":
            return

        if self.state == "I":
            self.ever_infected = True

        neighbors = self.model.grid.get_cell_list_contents([self.pos])

        for agent in neighbors:
            if agent.state == "S":
                if random.random() < .2:
                    agent.state = "E"
                    agent.infection_timer = 0

        
    def update_health(self):

        # become infected after exposure
        if self.state == "E":
            self.infection_timer += 1
            if self.infection_timer >10:
                self.state = "I"
                self.home_pos = self.pos

        # starvation and thirst
        self.hunger += .01
        self.thirst += .02

        # die of hunger/thirst if not infected, become infected if exposed
        if (self.hunger > 1.5 or self.thirst > 1.5) and self.state != "I" and self.state != "R":
            if self.state == "E": self.state = "I"          # after exposure, if citizen dies, they become infected
            else: self.state = "D"


    # see if the survivor has escaped the city (reached the edge of the grid)
    def check_escape(self):
        x, y = self.pos
        if x == 0 or y == 0 or x == self.model.width-1 or y == self.model.height-1:
            if self.state == "S":
                self.model.escaped += 1
                self.state = "R"

    def step(self):
        if self.state == "R":
            return

        self.move()
        self.infect_other()
        self.update_health()
        self.check_escape()




