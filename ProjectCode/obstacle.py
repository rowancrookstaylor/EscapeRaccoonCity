from mesa import Agent


class ObstacleAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)

        self.obstacle = True