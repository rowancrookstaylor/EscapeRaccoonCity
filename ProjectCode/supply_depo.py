from mesa import Agent
import random

class SupplyDepot(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.food = random.randint(10, 30)  # Random amount of food between 5 and 20
        self.water = random.randint(20, 50)  # Random amount of water between 10 and 30


    def has_resources(self):
        return self.food > 0 or self.water > 0

    def provide_resources(self, citizen):
        if self.food > 0:
            citizen.hunger = max(0, citizen.hunger - 0.2)  # Reduce hunger by 0.2)
            self.food -= 1  # Decrease food supply by 1

        if self.water > 0:
            citizen.thirst = max(0, citizen.thirst - 0.2)  # Reduce thirst by 0.2
            self.water -= 1  # Decrease water supply by 1

    def step(self):
        pass