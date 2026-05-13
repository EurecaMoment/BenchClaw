import carla

client = carla.Client("127.0.0.1", 2000)
client.set_timeout(60.0)
world = client.get_world()
print("Connected map:", world.get_map().name)
