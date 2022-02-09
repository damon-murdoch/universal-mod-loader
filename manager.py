# Operating System Libraries
import sys, os, shutil

# Get folder contents
import glob

# Json Parser Library
import json

class Mod:

    def __init__(self, path):

        # Get all of the items in the directory
        items = os.listdir(path)

        # Required items: 
        # content (folder containing mod)
        # content.json (config file)

        # If a config file is in the path
        if 'content.json' in items:

            # Build the path to the config file
            config_path = os.path.join(path, 'content.json')

            # Open and parse the config file
            config = json.load(open(config_path))

            # Mod name
            self.name = config['name']

            # Mod description
            self.desc = config['desc']

            # Mod source folder
            self.src = path

            # Mod destination folder
            self.dst = config['path']
        
        else: # No config file provided

            # Raise exception, this file is required
            raise Exception("NoContentJsonFileException")

        # If the content folder is in the path
        if 'content' in items:

            # Build the path to the content folder
            content_path = os.path.join(path, 'content')

            # Get the files in the mod folder (recursively)
            content_files = glob.glob(os.path.join(content_path, '**', '*.*'), recursive=True)

            # All of the files contained in the mod
            self.files = []

            # Loop over all of the files
            for file in content_files:

                # Add the file to the list of files to replace
                self.files.append(os.path.relpath(file, content_path))

        else: # No content folder provided

            # Raise exception, this file is required
            raise Exception("NoContentFolderException")


class Manager: 

    # mfl_template(void): Dict
    # Returns an empty mod file json dict object,
    # containing an empty mods list, a copied files
    # dictionary and a backup files dictionary.
    def mfl_template(self): 

        return {
            'mods': [], 
            'copied': {},
            'backup': {}
        }

    # mfl_add_mod(mfl: Dict, mod: String, copied: List, backup: List)
    # Given a mod file json dict, a mod name string, a list of files
    # that have been copied to the game and a list of files that were
    # backed up by the game adds the mod to the mods list, and adds
    # 
    def mfl_add_mod(self, mfl, mod, copied, backup):

        # Add the mod to the mods list
        mfl['mods'].append(mod)

        # Set the copied files list for the mod to the copied list
        mfl['copied'][mod] = copied

        # Loop over the backup files
        for file in backup:

            # If the file is already backed up
            if file in mfl['backup']:

                # Add the mod to the list of mods
                mfl['backup'][file].append(mod)

            else: # File not backed up yet

                # Create a new list containing the mod
                mfl['backup'][file] = [mod]

        # Return the mod file json object
        return mfl

    # mfl_rmv_mod(mfl: Dict, mod: String)
    # Given a mod file json dictionary and 
    # a mod name string, removes the mod 
    # from the mods list along with refs
    # to any file copied from this mod
    # or backed up from this mod only.

    # This function then returns the 
    # files which should be replaced
    # by the backed-up file and which
    # should be simply deleted.
    def mfl_rmv_mod(self, mfl, mod):

        # Remove the mod from the list of mods
        mfl['mods'].remove(mod)

        # Get the list of files to delete 
        # and remove it from the mfl obj
        delete = mfl['copied'].pop(mod)

        # Files to move (files only backed up by this mod)
        move = []

        # Files to copy (files backed up by this AND other mods)
        copy = []

        # List of file names backed up
        files = mfl['backup'].keys()

        # Loop over all of the backed-up files
        for file in list(files):

            # If the mods list contains the mod
            if mod in mfl['backup'][file]:

                # Remove it from the list
                mfl['backup'][file].remove(mod)

                # If there are any mods left
                if len(mfl['backup'][file]) > 0:

                    # Add file to copy list
                    copy.append(file)

                else: # No mods left

                    # Remove the file from the dict
                    mfl['backup'].pop(file)

                    # Add file to move list
                    move.append(file)

        print("Move", len(move), "Copy", len(copy))

        # Return the updated object, as well
        # as the list of files to delete,
        # move (from backup) and copy (from backup).
        return mfl, delete, move, copy

    # NEED TO KEEP:
    # List of installed mods, and the files they overwrote
    # Where those files are backed up, and where they should be stored

    def install(self, game_path, mod_path): 

        # Get the path to the mods database json file for the game
        mfl_path = os.path.join(game_path, 'mm_mods.json')

        # Check for a mods.json file in the game directory
        if not os.path.isfile(mfl_path):

            # mods: list of mods
            # copied: dict of file paths, with the mod that copied them (overwritten on already exist)
            # backedup: dict of file paths, with the mods that backed them up

            # Create a new empty mods.json file
            json.dump(self.mfl_template(), open(mfl_path, 'w+'))

        # Get the content from the mods json file 
        mfl = json.load(open(mfl_path))

        # If the mod is already in the mfl file
        if mod_path in mfl['mods']:

            print("Error: This mod has already been installed. Please uninstall before re-installing the mod again.")

        else: # Mod is not already installed

            # Create a mod object for the given mod
            mod = Mod(mod_path)

            # Source path to copy the files from
            src_path = os.path.join(mod_path, 'content')

            # Get the directory the file should be moved to
            dst_path = mod.dst.replace('$GAMEDIR', game_path)

            # Relative path, will be used when backing up files
            bkp_path = os.path.join(game_path, 'mm_backup', os.path.relpath(dst_path, game_path))

            # Files copied to game
            files_copied = []

            # Files backed up from game
            files_backed_up = []

            # Loop over all of the files in the mod
            for file in mod.files:

                # Get the source path for the file
                file_src_path = os.path.join(src_path, file)

                # Get the destination path for the file
                file_dst_path = os.path.join(dst_path, file)

                # If file already exists
                if os.path.exists(file_dst_path): 

                    # Full file backup path
                    file_bkp_path = os.path.join(bkp_path, file)

                    # # Backup does not already exist
                    if not os.path.exists(file_bkp_path): 

                        # Ensure that the backup path exists
                        os.makedirs(os.path.dirname(file_bkp_path), exist_ok=True)

                        # Back up the file to the destination
                        shutil.move(file_dst_path, file_bkp_path)

                    # Add to backed up list regardless, to 
                    # record that this file is required for
                    # another mod :)

                    # Append to backed up files
                    files_backed_up.append(file)

                # Ensure that the destination path exists
                os.makedirs(os.path.dirname(file_dst_path), exist_ok=True)

                # Copy the mod file to the destination
                shutil.copy(file_src_path, file_dst_path)

                # Record that the file has been written / replaced by the mod
                files_copied.append(file)

            # Update the mfl file with the new mod contents
            mfl = self.mfl_add_mod(mfl, mod_path, files_copied, files_backed_up)

            # Overwrite the existing file with the new content
            json.dump(mfl, open(mfl_path, 'w+'))


    # uninstall(game: String, mod: String): Void
    # Given the name of a game and a mod installed, 
    # attempts to uninstall the given mod from the
    # game based upon data stored by the manager.
    def uninstall(self, game_path, mod_path):

        # Get the path to the mods database json file for the game
        mfl_path = os.path.join(game_path, 'mm_mods.json')

        # Check for a mods.json file in the game directory
        if not os.path.isfile(mfl_path):

            # Cannot uninstall mod, no mods json file
            raise Exception("NoModsJsonFileException")

        # Get the content from the mods json file 
        mfl = json.load(open(mfl_path))

        # If the mod is in the mfl file
        if mod_path in mfl['mods']:

            # Create a mod object for the given mod
            mod = Mod(mod_path)
            
            # Get the directory the file should be moved to
            dst_path = mod.dst.replace('$GAMEDIR', game_path)

            # Relative path, will be used when backing up files
            bkp_path = os.path.join(game_path, 'mm_backup', os.path.relpath(dst_path, game_path))

            # Update the mods json file object (mfl) and retrieve the 
            # actions to perform on each file (delete, move, copy)
            mfl, delete, move, copy = self.mfl_rmv_mod(mfl, mod_path)

            # Files to delete
            for file in delete:

                # Remove the file from the game files
                os.remove(os.path.join(dst_path, file))

            # Files to copy
            for file in copy:

                # Copy the file from the backups
                shutil.copy(os.path.join(bkp_path, file), os.path.join(dst_path, file))

            # Files to move
            for file in move:

                # Move the file from the backups
                shutil.move(os.path.join(bkp_path, file), os.path.join(dst_path, file))
            
            # Overwrite the existing file with the new content
            json.dump(mfl, open(mfl_path, 'w+'))

        else: # Mod is not installed

            raise  Exception("ModNotInstalledException")

# If we are calling this directly
if __name__ == '__main__': 

    # How to use:
    # Install Mod:
    # python manager.py install path-to-game path-to-mod
    # 
    # Uninstall Mod:
    # python manager.py uninstall path-to-game path-to-mod

    # Get the command line arguments
    args = sys.argv[1:]

    try:

        # 3 args, excluding filename
        if len(args) == 3:

            # Create a new empty manager object
            manager = Manager()

            # Install / Uninstall command
            command = args[0]

            # Game to install mod for
            game = args[1]

            # Mod to install
            mod = args[2]

            # Install Mod
            if command == 'install': 

                # Perform the mod install
                manager.install(game, mod)

            # Uninstall Mod
            elif command == 'uninstall': 

                # Perform the mod uninstall
                manager.uninstall(game, mod)

            else: # Unrecognised command

                # Raise unrecognised command exception
                raise Exception("Failed: Unrecognised command '" + command + "'.")

        else: # Wrong arguments

            # Raise wrong argument count exception
            raise Exception("3 arguments required. Number provided:", len(args))

    except Exception as e: # General error catch

        print("Failed:", e, "error.")

        print("Usage: python manager.py [command] path-to-game path-to-mod")
        print("Where command is one of: install, uninstall")