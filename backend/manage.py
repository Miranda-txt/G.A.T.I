import sys

from config.env import configure

if __name__ == "__main__":
    configure()
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
