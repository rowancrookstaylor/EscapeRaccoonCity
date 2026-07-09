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

        # needs
        self.hunger = random.uniform(0,1)
        self.thirst = random.uniform(0,1)

        # movement
        self.speed = 1

    def distance_to_edge(self, pos):
        x, y = pos
        center_x = self.model.width / 2
        center_y = self.model.height / 2
        return math.sqrt((x - center_x)**2 + (y - center_y)**2)

    def move(self):
        if self.state == "I":
            self.speed = .5
        else:
            self.speed = 1

        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False)

        best_cell = None
        best_score = float("inf")

        for cell in neighbors:
            dist = self.distance_to_edge(cell)

            # bias toward edge
            score = dist + random.random()

            if score < best_score:
                best_score = score
                best_cell = cell

        if best_cell:
            self.model.grid.move_agent(self, best_cell)


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

        # starvation and thirst
        self.hunger += .01
        self.thirst += .02

        # die of hunger/thirst if not infected, become infected if exposed
        if (self.hunger > 1.5 or self.thirst > 1.5) and self.state != "I" and self.state != "R":
            if self.state == "E": self.state = "I"          # after exposure, if citizen dies, they become infected
            else: self.state = "D"

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




