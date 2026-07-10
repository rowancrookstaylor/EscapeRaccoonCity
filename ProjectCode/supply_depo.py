from mesa import Agent
import random

class SupplyDepot(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.food = random.randint(10, 30)  # Random amount of food between 5 and 20
        self.water = random.randint(20, 50)  # Random amount of water between 10 and 30
        self.weapons = random.randint(1,3)


    def has_resources(self):
        return self.food > 0 or self.water > 0

    def has_weapons_stock(self):
        return self.weapons > 0

    def provide_resources(self, citizen):
        if self.food > 0:
            citizen.hunger = max(0, citizen.hunger - 0.2)  # Reduce hunger by 0.2)
            self.food -= 1  # Decrease food supply by 1

        if self.water > 0:
            citizen.thirst = max(0, citizen.thirst - 0.2)  # Reduce thirst by 0.2
            self.water -= 1  # Decrease water supply by 1

    def provide_weapon(self, citizen):

        # only give weapons to healthy citizens
        if citizen.state != "S":
            return False

        if citizen.age_group == "Child":
            return False # chidlren cannot pick up weapons

        # citizen cannot carry multiple weapons
        if citizen.has_weapon:
            return False

        # depot must have weapons
        if self.weapons <= 0:
            return False


        citizen.has_weapon = True
        citizen.weapon_attempts = 0

        self.weapons -= 1

        return True


    def step(self):
        pass