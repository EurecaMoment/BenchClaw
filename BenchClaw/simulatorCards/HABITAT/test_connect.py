import importlib.metadata as md

import habitat
import habitat_sim


print("habitat-sim:", md.version("habitat-sim"))
print("habitat-lab:", md.version("habitat-lab"))
print("habitat_sim path:", habitat_sim.__file__)
print("habitat path:", habitat.__file__)
