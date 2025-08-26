import os
import getpass

from gamestates import main

from load_photos import cleanup_temp_dirs

try:
    os.remove("auto.pick")
except Exception:
    pass

if __name__ == "__main__":
    try:
        if getpass.getuser() == "lunamidori":
            import cProfile
            cProfile.run('main(1)', filename='profiling_results.prof')
        else:
            main(1)
        
        cleanup_temp_dirs()
    except Exception as error:
        print(f"A error: {str(error)}")