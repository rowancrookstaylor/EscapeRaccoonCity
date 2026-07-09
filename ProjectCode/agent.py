from mesa import Agent
import random
import math
from supply_depo import SupplyDepot
import heapq



class CitizenAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.obstacle = False  # obstacle state (True if the agent is an obstacle)

        # infection state (healthy = s, exposed = e, infected = i, dead = d, escaped = r)
        self.state = "S"
        self.infection_timer = 0
        self.ever_infected = False

        self.hunger = random.uniform(0,1)   # needs
        self.thirst = random.uniform(0,1)

        self.speed = 1  # movement
      
        self.home_pos = None    # home position (for infected)

        self.vision_radius = 8 # vision radius for infected to detect survivors
        self.infection_radius = 1  # infection radius for infected to infect survivors

        self.aware = False
        self.citizen_vision_radius = 10

        self.target_depot = None  # target supply depot for survivors

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_star(self, start, goal):
        frontier = []
        heapq.heappush(frontier, (0, start))

        came_from = {}
        cost_so_far = {}

        came_from[start] = None
        cost_so_far[start] = 0

        while frontier:
            current = heapq.heappop(frontier)[1]
            
            if current == goal:
                break

            neighbors = self.model.grid.get_neighborhood(current, moore=True, include_center=False)

            for next_cell in neighbors:
                if self.is_blocked(next_cell):
                    continue

                new_cost = cost_so_far[current] + 1  # Assuming uniform cost for movement
                if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
                    cost_so_far[next_cell] = new_cost

                    priority = (new_cost + self.heuristic(next_cell,goal))

                    heapq.heappush(frontier, (priority, next_cell))

                    came_from[next_cell] = current

        if goal not in came_from:
            return None  # No path found

        path =[]
        current = goal

        while current != start:
            path.append(current)
            current = came_from[current]

        path.reverse()

        return path

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

    # get supplies if needed
    def find_nearby_depots(self):
        depots = []
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True, radius = 20)

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])
            for agent in agents:
                if agent.__class__.__name__ == "SupplyDepot" and agent.has_resources():
                    depots.append(agent)
        return depots

    def needs_supplies(self): # determine need for supplies based on hunger and thirst levels
        return self.hunger > .7 or self.thirst > 0.7

    def move_towards_depot(self): #move towards the closest supply depot if there is one
        depots = self.find_nearby_depots()
        if not depots:
            return False  # No depots found

        closest = min(depots, key=lambda depot: self.distance_to(depot.pos))
        
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)

        best_cell = min(neighbors, key=lambda cell: self.distance_between(cell, closest.pos))

        self.model.grid.move_agent(self, best_cell)

        if self.pos == closest.pos:
            closest.provide_resources(self)

        return True  # Moved towards a depot



    # avoid infected
    def detect_infected(self):
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=self.citizen_vision_radius)
        
        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])

            for agent in agents:
                if hasattr(agent, "state") and agent.state == "I":
                    return True
        return False

    def normal_move(self):
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)

        if neighbors: self.model.grid.move_agent(self, random.choice(neighbors))

    def is_blocked(self, pos):
        agents = self.model.grid.get_cell_list_contents([pos])
        for agent in agents:
            if hasattr(agent, "obstacle") and agent.obstacle:
                return True
        return False

    """ old escape move before adding A* ;;; will delete later its just here for reference:
    # move towards exit
    def escape_move(self):
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
            """

    def escape_move(self):
        exits = []
        for x in range(self.model.width):
            exits.append((x,0))
            exits.append((x,self.model.height-1))

        for y in range(self.model.height):
            exits.append((0,y))
            exits.append((self.model.width-1,y))

        goal = min(exits, key=lambda exit: self.distance_to(exit))

        path = self.a_star(self.pos, goal)

        if path:
            next_step = path[0]
            self.model.grid.move_agent(self, next_step)



# MOVEMENT FOR THE INFECTED
    # helper functions for infected movement
    def distance_from_home(self,pos):
        if self.home_pos is None: self.home_pos = self.pos

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
                if hasattr(agent, "state") and agent.state in ["S", "E"]:
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
                distance = self.distance_between(cell, target.pos)

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

# normal move fuction
    def move(self):
        if self.state == "I":
            self.infected_move()

        elif self.state in ["S", "E"]:
            if self.needs_supplies():
                got_supplies = self.move_towards_depot()

                if got_supplies:
                    return  # moved towards depot, skip other movement

            if self.detect_infected():
                self.aware = True

            if self.aware:
                self.escape_move()
            else:
                self.normal_move()


    # spread infection (if infected)
    def infect_other(self):
        if self.state != "I":
            return

        if self.state == "I":
            self.ever_infected = True

        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True,radius=self.infection_radius)

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])

            for agent in agents:
                if hasattr(agent, "state") and agent.state == "S":
                    if random.random() < .9:
                        agent.state = "E"
                        agent.infection_timer = 0

        
    def update_health(self):

        # become infected after exposure
        if self.state == "E":
            self.infection_timer += 1
            if self.infection_timer >3:
                self.state = "I"
                self.home_pos = self.pos
                self.obstacle = True  # infected become obstacles to survivors

        # starvation and thirst
        self.hunger += .01
        self.thirst += .02

        # die of hunger/thirst if not infected, become infected if exposed
        if (self.hunger > 1.2 or self.thirst > 1.2) and self.state != "I" and self.state != "R":
            if self.state == "E": 
                self.state = "I"          # after exposure, if citizen dies, they become infected
                self.home_pos = self.pos
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




