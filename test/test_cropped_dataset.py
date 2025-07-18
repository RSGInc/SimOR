import subprocess
import os
import sys

def test_cropped_example():

    file_path = os.path.join(os.path.dirname(__file__), "../simulation.py")

    run_args = [
        "-c", "configs",  # Config directory
        "-d", "model_data/metro_data_cropped",  # Input data directory
        "-o", "outputs/test"  # Output directory
    ]

    if os.environ.get("GITHUB_ACTIONS") == "true":
        subprocess.run(["coverage", "run", "-a", file_path] + run_args, check=True)
    else:
        subprocess.run([sys.executable, file_path] + run_args, check=True)
    
    return True


if __name__ == "__main__":
    test_cropped_example()