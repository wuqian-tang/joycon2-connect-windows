"""Console bootloader keeps the redirected worker line protocol intact."""
import sys
from joycon2_assistant.worker import main

if __name__ == '__main__':
    sys.exit(main())
