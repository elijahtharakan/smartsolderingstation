"""Convenient launcher for the demo.

Run this from the project root to start the demo without worrying about PYTHONPATH:

    python run_demo.py --robot mock

This simply delegates to `src.demo.main`.
"""
from src import demo
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", choices=["mock", "serial", "gpio"], default="mock")
    args = parser.parse_args()
    demo.main(robot_type=args.robot)


if __name__ == '__main__':
    main()
