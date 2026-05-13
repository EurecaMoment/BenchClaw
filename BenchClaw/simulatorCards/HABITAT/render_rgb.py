import os
from pathlib import Path

from PIL import Image
import habitat_sim


SCENE = "/home/maqiang/simulators/habitat/data/scene_datasets/habitat-test-scenes/skokloster-castle.glb"
OUT = "/home/maqiang/benchclaw/simulator_cards/HABITAT/output/first_rgb.png"


Path(OUT).parent.mkdir(parents=True, exist_ok=True)

sim_cfg = habitat_sim.SimulatorConfiguration()
sim_cfg.scene_id = SCENE
sim_cfg.gpu_device_id = 0

sensor_spec = habitat_sim.CameraSensorSpec()
sensor_spec.uuid = "color_sensor"
sensor_spec.sensor_type = habitat_sim.SensorType.COLOR
sensor_spec.resolution = [480, 640]
sensor_spec.position = [0.0, 1.5, 0.0]

agent_cfg = habitat_sim.agent.AgentConfiguration()
agent_cfg.sensor_specifications = [sensor_spec]

cfg = habitat_sim.Configuration(sim_cfg, [agent_cfg])
sim = habitat_sim.Simulator(cfg)
sim.initialize_agent(0)
obs = sim.get_sensor_observations()

Image.fromarray(obs["color_sensor"][:, :, :3]).save(OUT)

print("Habitat-Sim started successfully.")
print("Saved RGB frame:", OUT)

sim.close()
