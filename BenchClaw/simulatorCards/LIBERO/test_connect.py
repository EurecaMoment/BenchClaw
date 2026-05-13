import importlib.metadata as md
import os

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

print("python executable check done")
print("libero package:", md.version("libero"))
print("robosuite package:", md.version("robosuite"))

from libero.libero import benchmark
from libero.libero.envs import OffScreenRenderEnv

suite = benchmark.get_benchmark_dict()["libero_10"]()
task = suite.get_task(0)
print("benchmark task name:", task.name)
print("benchmark task language:", task.language)
print("OffScreenRenderEnv import OK:", OffScreenRenderEnv)
