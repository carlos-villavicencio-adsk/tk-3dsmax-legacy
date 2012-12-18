"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Menu handling for Nuke

"""

import tank
import platform
import sys
import os
import unicodedata
from Py3dsMax import mxs


TANK_MENU_NAME = "Tank"


class MenuGenerator(object):
    """
    Menu generation functionality for 3dsmax
    """

    def __init__(self, engine):
        self._engine = engine
        self._dialogs = []

    ##########################################################################################
    # public methods

    def create_menu(self):
        """
        Render the entire Tank menu.
        """
        # create main menu
        tank_menu = self._create_tank_menu()
        
        item = mxs.menuMan.createSeparatorItem()
        
        tank_menu.addItem(item, -1)
        
        
        
        return
        
        # now add the context item on top of the main menu
        self._context_menu = self._add_context_menu()
        self._menu_handle.addSeparator()

        # now enumerate all items and create menu objects for them
        menu_items = []
        for (cmd_name, cmd_details) in self._engine.commands.items():
             menu_items.append( AppCommand(cmd_name, cmd_details) )


        # now add favourites
        for fav in self._engine.get_setting("menu_favourites"):
            app_instance_name = fav["app_instance"]
            menu_name = fav["name"]
            
            # scan through all menu items
            for cmd in menu_items:                 
                 if cmd.get_app_instance_name() == app_instance_name and cmd.name == menu_name:
                     # found our match!
                     cmd.add_command_to_menu(self._menu_handle)
                     # mark as a favourite item
                     cmd.favourite = True            

        self._menu_handle.addSeparator()
        
        
        # now go through all of the menu items.
        # separate them out into various sections
        commands_by_app = {}
        
        for cmd in menu_items:
                        
            if cmd.get_type() == "node":
                # add to the node menu
                # get icon if specified - default to tank icon if not specified
                icon = cmd.properties.get("icon", self.tank_logo)
                self._node_menu_handle.addCommand(cmd.name, cmd.callback, icon=icon)
                
            elif cmd.get_type() == "custom_pane":
                # custom pane
                # add to the std pane menu in nuke
                icon = cmd.properties.get("icon")
                self._pane_menu.addCommand(cmd.name, cmd.callback, icon=icon)
                # also register the panel so that a panel restore command will
                # properly register it on startup or panel profile restore.
                nukescripts.registerPanel(cmd.properties.get("panel_id", "undefined"), cmd.callback)
                
            elif cmd.get_type() == "context_menu":
                # context menu!
                cmd.add_command_to_menu(self._context_menu)
                
            else:
                # normal menu
                app_name = cmd.get_app_name()
                if app_name is None:
                    # un-parented app
                    app_name = "Other Items" 
                if not app_name in commands_by_app:
                    commands_by_app[app_name] = []
                commands_by_app[app_name].append(cmd)
        
        # now add all apps to main menu
        self._add_app_menu(commands_by_app)
            
            
    def destroy_menu(self):
        pass
            # todo!
        
    ##########################################################################################
    # context menu and UI

    def _create_tank_menu(self):
        # create the tank menu
        if mxs.menuMan.findMenu(TANK_MENU_NAME) is None:
            # no tank menu - so create it!
            menu_item = mxs.menuMan.createMenu(TANK_MENU_NAME)
            sub_menu = mxs.menuMan.createSubMenuItem(TANK_MENU_NAME, menu_item)
            
            # figure out the menu index - place after MAXScript menu
            main_menu = mxs.menuMan.getMainMenuBar()
            tank_menu_idx = 1
            for idx in range(main_menu.numItems()):
                # indices are one based
                menu_idx = idx+1
                if main_menu.getItem(menu_idx).getTitle() == "&MAXScript":
                    tank_menu_index = menu_idx+1
                    break
            
            main_menu.addItem(sub_menu, tank_menu_index)
            mxs.menuMan.updateMenuBar()
        
        return mxs.menuMan.findMenu(TANK_MENU_NAME)
    
    
    
    def _add_context_menu(self):
        """
        Adds a context menu which displays the current context
        """        
        
        ctx = self._engine.context
        
        if ctx.entity is None:
            # project-only!
            ctx_name = "%s" % ctx.project["name"]
        
        elif ctx.step is None and ctx.task is None:
            # entity only
            # e.g. Shot ABC_123
            ctx_name = "%s %s" % (ctx.entity["type"], ctx.entity["name"])

        else:
            # we have either step or task
            task_step = None
            if ctx.step:
                task_step = ctx.step.get("name")
            if ctx.task:
                task_step = ctx.task.get("name")
            
            # e.g. [Lighting, Shot ABC_123]
            ctx_name = "%s, %s %s" % (task_step, ctx.entity["type"], ctx.entity["name"])
        
        # create the menu object        
        ctx_menu = self._menu_handle.addMenu(ctx_name)
        ctx_menu.addCommand("Jump to Shotgun", self._jump_to_sg)
        ctx_menu.addCommand("Jump to File System", self._jump_to_fs)
        ctx_menu.addSeparator()
        
        return ctx_menu
                        
    
    def _jump_to_sg(self):

        if self._engine.context.entity is None:
            # project-only!
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       "Project", 
                                       self._engine.context.project["id"])
        else:
            # entity-based
            url = "%s/detail/%s/%d" % (self._engine.shotgun.base_url, 
                                       self._engine.context.entity["type"], 
                                       self._engine.context.entity["id"])
        
        # deal with fucked up nuke unicode handling
        if url.__class__ == unicode:
            url = unicodedata.normalize('NFKD', url).encode('ascii', 'ignore')
        nukescripts.openurl.start(url)
        
        
    def _jump_to_fs(self):
        
        """
        Jump from context to FS
        """
        
        if self._engine.context.entity:
            paths = self._engine.tank.paths_from_entity(self._engine.context.entity["type"], 
                                                     self._engine.context.entity["id"])
        else:
            paths = self._engine.tank.paths_from_entity(self._engine.context.project["type"], 
                                                     self._engine.context.project["id"])
        
        # launch one window for each location on disk
        # todo: can we do this in a more elegant way?
        for disk_location in paths:
                
            # get the setting        
            system = platform.system()
            
            # run the app
            if system == "Linux":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "Darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "Windows":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)
            
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
        
            
    ##########################################################################################
    # app menus
        
        
    def _add_app_menu(self, commands_by_app):
        """
        Add all apps to the main menu, process them one by one.
        """
        for app_name in sorted(commands_by_app.keys()):
            
            
            if len(commands_by_app[app_name]) > 1:
                # more than one menu entry fort his app
                # make a sub menu and put all items in the sub menu
                app_menu = self._menu_handle.addMenu(app_name)
                for cmd in commands_by_app[app_name]:
                    cmd.add_command_to_menu(app_menu)
            
            else:
                # this app only has a single entry. 
                # display that on the menu
                # todo: Should this be labelled with the name of the app 
                # or the name of the menu item? Not sure.
                cmd_obj = commands_by_app[app_name][0]
                if not cmd_obj.favourite:
                    # skip favourites since they are alreay on the menu
                    cmd_obj.add_command_to_menu(self._menu_handle)
                                
        
        
    
            
class AppCommand(object):
    """
    Wraps around a single command that you get from engine.commands
    """
    
    def __init__(self, name, command_dict):        
        self.name = name
        self.properties = command_dict["properties"]
        self.callback = command_dict["callback"]
        self.favourite = False
        
        
    def get_app_name(self):
        """
        Returns the name of the app that this command belongs to
        """
        if "app" in self.properties:
            return self.properties["app"].display_name
        return None
        
    def get_app_instance_name(self):
        """
        Returns the name of the app instance, as defined in the environment.
        Returns None if not found.
        """
        if "app" not in self.properties:
            return None
        
        app_instance = self.properties["app"]
        engine = app_instance.engine

        for (app_instance_name, app_instance_obj) in engine.apps.items():
            if app_instance_obj == app_instance:
                # found our app!
                return app_instance_name
            
        return None
        
    def get_documentation_url_str(self):
        """
        Returns the documentation as a str
        """
        if "app" in self.properties:
            app = self.properties["app"]
            doc_url = app.documentation_url
            # deal with nuke's inability to handle unicode. #fail
            if doc_url.__class__ == unicode:
                doc_url = unicodedata.normalize('NFKD', doc_url).encode('ascii', 'ignore')
            return doc_url

        return None
        
    def get_type(self):
        """
        returns the command type. Returns node, custom_pane or default
        """
        return self.properties.get("type", "default")
        
    def add_command_to_menu(self, menu):
        """
        Adds an app command to the menu
        """
        # std shotgun menu
        icon = self.properties.get("icon")
        menu.addCommand(self.name, self.callback, icon=icon) 














    