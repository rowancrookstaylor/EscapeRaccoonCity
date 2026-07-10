from mesa import Agent
import random
import math
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
        
        self.has_weapon = False
        self.weapon_attempts = 0
        self.max_weapon_attempts = 6

        self.speed = 1  # movement
      
        self.home_pos = None    # home position (for infected)

        self.vision_radius = 6 # vision radius for infected to detect survivors
        self.infection_radius = 1  # infection radius for infected to infect survivors

        self.aware = False
        self.citizen_vision_radius = 10
        self.social_radius = 3 # for social force implementation

        self.target_depot = None  # target supply depot for survivors

        self.current_path = []
        self.path_target = None

        # weights for utility function
        self.escape_weight = random.uniform(0.8,1.2)
        self.supply_weight = random.uniform(0.8,1.2)
        self.risk_weight = random.uniform(0.8,1.2)




# Utlity functions
    def calculate_escape_utility(self):
    # calculate the value of escape
        distance = self.distance_to(self.get_closest_exit())

        distance_score = 1 / (distance + 1)
        danger_score = 0
        if self.detect_infected():
            danger_score = 1

        utility = (distance_score * self.escape_weight) + (danger_score * self.risk_weight)

        return utility

    def calculate_supply_utility(self):
    # calculate the value of getting supplies
        hunger_need = self.hunger
        thirst_need = self.thirst

        need_score = hunger_need + thirst_need

        depots = self.find_nearby_depots()

        if not depots:
            return 0

        closest = min(depots, key=lambda depots:self.distance_to(depots.pos))

        distance = self.distance_to(closest.pos)

        distance_score = 1/(distance+1)

        utility = (need_score * self.supply_weight + distance_score)

        return utility


# social force implementation
    def goal_force(self, target):
    # desire to reach a destination/gives them a direction
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]

        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return (0,0)
        return (dx/distance, dy/distance)

    def citizen_repulsion(self):
    # prevents collision
        force_x = 0
        force_y = 0
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False,radius=self.social_radius)

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])
            for agent in agents:
                if agent != self and hasattr(agent,"state") and agent.state in ["S","E"]:
                    dx = self.pos[0] - agent.pos[0]
                    dy = self.pos[1] - agent.pos[1]

                    distance = math.sqrt(dx**2 + dy**2)
                    if distance > 0:
                        strength = 1 / distance
                        force_x += (dx /distance) * strength
                        force_y ++ (dy/distance) * strength
        return (force_x, force_y)

    def zombie_repulsion(self):
        force_x = 0
        force_y = 0

        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center= False, radius = self.citizen_vision_radius)

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])

            for agent in agents:
                if hasattr(agent,"state") and agent.state == "I":
                    dx = self.pos[0] - agent.pos[0]
                    dy = self.pos[1] - agent.pos[1]

                    distance = math.sqrt(dx**2 + dy**2)

                    if distance > 0:
                        strength = 5 / distance
                        force_x += (dx/distance) * strength
                        force_y += (dy/distance) * strength
        return (force_x,force_y)

    def social_force_move(self, target):
        goal_x, goal_y = self.goal_force(target)
        people_x, people_y = self.citizen_repulsion()
        zombie_x, zombie_y = self.zombie_repulsion()

        total_x = (goal_x + people_x + zombie_x)
        total_y = (goal_y + people_y + zombie_y)

        neighbors = self.model.grid.get_neighborhood(self.pos,moore=True,include_center=False)
        
        best_cell = None
        best_score = -999

        for cell in neighbors:
            movement_x = cell[0] - self.pos[0]
            movement_y = cell[1] - self.pos[1]

            score = (movement_x * total_x + movement_y * total_y)

            if not self.is_blocked(cell):
                if score > best_score:
                    best_score = score
                    best_cell = cell
        if best_cell:
            self.model.grid.move_agent(self, best_cell)


        
# A* pathfinding algorithm for survivor movement
    def heuristic(self, a, b): #functionally the same as distance_between but i kept it for the sake of maintaining the expected structure/keywords for the A* function
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_star(self, start, goal):
    # main A* pathfinding function
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

                base_cost = 1
                danger = self.danger_cost(next_cell)
                new_cost = cost_so_far[current] + base_cost + danger

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
  
    def danger_cost(self, pos):
        agents = self.model.grid.get_cell_list_contents([pos])

        for agent in agents:
            if hasattr(agent, "state") and agent.state == "I":
                return 50

        neighbors = self.model.grid.get_neighborhood(pos, moore=True, include_center=False)

        for cell in neighbors:
            agents = self.model.grid.get_cell_list_contents([cell])

            for agent in agents:
                if hasattr(agent, "state") and agent.state == "I":
                    return 10
        return 0

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
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] -pos2[1])

# MOVEMENT FOR THE SURVIVORS

    def find_nearby_depots(self):
        # get supplies if needed
        depots = []
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True, radius = 20)

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])
            for agent in agents:
                if agent.__class__.__name__ == "SupplyDepot" and agent.has_resources():
                    depots.append(agent)
        return depots

    def needs_supplies(self): 
    # determine need for supplies based on hunger and thirst levels
        return self.hunger > .7 or self.thirst > 0.7

    def move_towards_depot(self): 
    # move towards the closest supply depot if there is one
        depots = self.find_nearby_depots()
        if not depots:
            return False  # No depots found

        closest = min(depots, key=lambda depot: self.distance_to(depot.pos))
        
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)

        self.social_force_move(closest.pos)

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


    def escape_move(self):
        if not self.current_path or self.path_target is None:
            goal = self.get_closest_exit()
            path = self.a_star(self.pos, goal)

            if path:
                self.current_path = path
                self.path_target = goal

        if self.current_path:
            target = self.current_path[0]
            self.social_force_move(target)

    def get_closest_exit(self):
        return min(self.model.exits, key=lambda e: self.distance_to(e))


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
            escape_utility = self.calculate_escape_utility()
            supply_utility = self.calculate_supply_utility()

            if supply_utility > escape_utility:
                got_supplies = self.move_towards_depot()
                if got_supplies: return
            else:
                if self.detect_infected():
                    self.aware = True
                    self.current_path = []

                    if self.aware:
                        if random.random() < .2:
                            self.current_path = []

                        self.escape_move()
                    else: self.normal_move()

# combat from citizens
    def pickup_weapon(self):
        cells = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=True,
            radius=1
        )

        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])

            for agent in agents:
                if agent.__class__.__name__ == "SupplyDepot":
                    if agent.has_weapons_stock():
                        return agent.provide_weapon(self)

        return False

    def shoot_zombie(self):

        if not self.has_weapon:
            return

        if self.weapon_attempts >= self.max_weapon_attempts:
            self.has_weapon = False
            return


        cells = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=True,
            radius=2
        )


        for cell in cells:
            agents = self.model.grid.get_cell_list_contents([cell])
            for agent in agents:
                if hasattr(agent,"state") and agent.state == "I":

                    self.weapon_attempts += 1

                    # 20% chance to kill zombie
                    if random.random() < .2:
                        agent.state = "D"
                        agent.obstacle = False

                    # only shoot one zombie per attempt
                    return

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
                    if random.random() < .5:
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
        if (self.hunger > 1.0 or self.thirst > 1.0) and self.state != "I" and self.state != "R":
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
        if self.state in ["R", "D"]:
            return

        if self.state == "S":
            self.pickup_weapon()
            self.shoot_zombie()

        self.move()
        self.infect_other()
        self.update_health()
        self.check_escape()




