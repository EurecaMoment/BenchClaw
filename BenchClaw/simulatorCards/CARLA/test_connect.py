import argparse

import carla


def main():
    parser = argparse.ArgumentParser(description="Connect to a CARLA server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    client = carla.Client(args.host, args.port)
    client.set_timeout(args.timeout)
    world = client.get_world()
    print("Connected map:", world.get_map().name)


if __name__ == "__main__":
    main()
