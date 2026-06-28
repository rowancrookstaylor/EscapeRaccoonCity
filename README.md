# EscapeRaccoonCity
modeling and simulation project repo

-------------------------------------------

## project status
implemented zombie model, citizen agent, a grid, and a scheduler
still need to implement A*, updates to zombie behavior, supply depos, and citizen health stats

##installation instructions
requries: python 3.14, mesa 1.2.1 (NOT 2.x), numpy, networkx

setup: download and unzip repo folder, all files are in folder titled ProjectCode

##Usage
**steps:** 
1. navigate to ProjectCode solution folder
2. run main.py --- broswer should open automatically

##Architecture Overview
**Model Class (ZombieModel)**: corresponds to the UML Simulation Environment / Controller, responsible for initialization, scheduling, and global metrics.

**Agent Class (CitizenAgent)**: corresponds to the UML Entity/Agent, encapsulating state, behavior, and local decision-making.

**Grid (MultiGrid)**: corresponds to the UML Spatial Environment, representing a discrete 2D bounded space.

**Scheduler (RandomActivation)**: corresponds to the UML Execution Manager, controlling agent update order per timestep.
