"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

A Houdini engine for Tank.

"""

# std libs
import os
import sys
import pickle
import logging
import platform
import textwrap

# tank libs
import tank

# application libs


CONSOLE_OUTPUT_WIDTH = 120

class MaxEngine(tank.platform.Engine):
    def init_engine(self):
        self.log_debug("%s: Initializing..." % self)
        
        # now check that there is a location on disk which corresponds to the context
        # for the 3ds Max engine (because it for example sets the 3ds Max project)
        if len(self.context.entity_locations) == 0:
            # Try to create path for the context.
            self.tank.create_filesystem_structure(self.context.entity["type"], self.context.entity["id"])
            
            if len(self.context.entity_locations) == 0:
                raise tank.TankError("No folders on disk are associated with the current context. The Houdini "
                    "engine requires a context which exists on disk in order to run correctly.")

    def destroy_engine(self):
        self.log_debug('%s: Destroying...' % self)

    def log_debug(self, msg):
        sys.stdout.write(str(msg)+'\n')

    def log_info(self, msg):
        sys.stdout.write(str(msg)+'\n')

    def log_error(self, msg):
        sys.stdout.write(str(msg)+'\n')
        
    def log_warning(self, msg):
        sys.stdout.write(str(msg)+'\n')
