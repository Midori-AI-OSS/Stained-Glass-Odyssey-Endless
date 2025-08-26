import os
import sys
import random
import shutil
import tempfile
import platform

from halo import Halo

from typing import List

spinner = Halo(text='Loading', spinner='dots', color='green')

TEMP_DIRS = []

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    If possible, load the resource into memory (RAM disk or temporary directory).

    Args:
        relative_path: The relative path to the resource.

    Returns:
        The absolute path to the resource in memory, or the original path if loading into memory fails.
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_path, relative_path)

    try:
        if not os.path.isfile(full_path):
            return full_path

        if platform.system() == "Windows":
            temp_dir = tempfile.mkdtemp(prefix="resource_")
        elif platform.system() == "Linux":
            temp_dir = tempfile.mkdtemp(prefix="resource_", dir="/dev/shm")
        else:
            temp_dir = tempfile.mkdtemp(prefix="resource_")
        
        TEMP_DIRS.append(temp_dir) # Store temp dir for cleanup

        resource_name = os.path.basename(relative_path)
        temp_resource_path = os.path.join(temp_dir, resource_name)
        shutil.copy2(full_path, temp_resource_path)

        return temp_resource_path
    except OSError as e:
        print(f"Failed to load resource into memory: {e}. Falling back to original path.")
        return full_path
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Falling back to original path.")
        return full_path


def cleanup_temp_dirs():
    """
    Clean up all temporary directories created by resource_path.
    """
    for temp_dir in TEMP_DIRS:
        spinner.start(text=f"Successfully cleaned up temporary directory: {temp_dir}")
        try:
            shutil.rmtree(temp_dir)
        except OSError as e:
            spinner.fail(text=f"Failed to clean up temporary directory {temp_dir}: {e}")
    
    spinner.succeed(text="Successfully cleaned up temporary directorys")

def set_photo(photo: str) -> str:
    """
    Sets the photo to be displayed based on the given photo name.

    Args:
        photo: The name of the photo to display (without extension).

    Returns:
        The absolute path to the photo, or a fallback photo if the specified photo is not found.
    """
    photo_path = resource_path(os.path.join("photos", f"{photo}.png"))
    if os.path.exists(photo_path):
        return photo_path
    else:
        fallback_dir = resource_path(os.path.join("photos", "fallbacks"))
        photos = os.listdir(fallback_dir)
        return resource_path(os.path.join(fallback_dir, random.choice(photos)))

def set_themed_photo(photo: str) -> str:
    """
    Sets a themed photo to be displayed based on a search term.

    Args:
        photo: The search term to use when looking for a themed photo.

    Returns:
        The absolute path to a randomly chosen themed photo, or a fallback photo if no themed photos are found.
    """
    photos: List[str] = []

    for root, _, files in os.walk(resource_path("photos")):
        for f in files:
            if photo in f and f.endswith(".png"):
                photos.append(os.path.join(root, f))

    if photos:
        return random.choice(photos)
    else:
        fallback_dir = resource_path(os.path.join("photos", "fallbacks"))
        photos = os.listdir(fallback_dir)
        return resource_path(os.path.join(fallback_dir, random.choice(photos)))

def set_themed_dot_photo(photo: str) -> str:
    """
    Sets a themed photo to be displayed based on a search term.

    Args:
        photo: The search term to use when looking for a themed photo.

    Returns:
        The absolute path to a randomly chosen themed photo, or a fallback photo if no themed photos are found.
    """
    photos: List[str] = []
        
    for root, _, files in os.walk(resource_path(os.path.join("photos", "dots", photo))):
        for f in files:
            if photo in f and f.endswith(".png"):
                photos.append(os.path.join(root, f))

    if photos:
        return random.choice(photos)
    else:
        fallback_dir = resource_path(os.path.join("photos", "fallbacks"))
        photos = os.listdir(fallback_dir)
        return resource_path(os.path.join(fallback_dir, random.choice(photos)))

def set_bg_photo() -> str:
    """
    Sets a random background photo to be displayed.

    Returns:
        The absolute path to a randomly chosen background photo.
    """
    bg_dir = resource_path(os.path.join("photos", "background"))
    photos = os.listdir(bg_dir)
    return resource_path(os.path.join(bg_dir, random.choice(photos)))

def set_bg_music() -> str:
    """
    Sets a random background music file to be played.

    Returns:
        The absolute path to a randomly chosen background music file.
    """
    music_dir = resource_path(os.path.join("music", "background"))
    musics = os.listdir(music_dir)
    return resource_path(os.path.join(music_dir, random.choice(musics)))