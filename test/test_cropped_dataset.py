import subprocess
import sys
import os

def test_cropped_example():
    file_path = os.path.join(os.path.dirname(__file__), "../simulation.py")

    subprocess.run(
        [
            "coverage",  # Command to run coverage
            "run",  # Command to run the script
            "-a",  # Append coverage data
            file_path,  # Path to the script
            "-c", "configs",  # Config directory
            "-d", "model_data/cropped_data",  # Input data directory
            "-o", "outputs/test"  # Output directory
        ], 
        check=True
    )
    
    return True


if __name__ == "__main__":
    test_cropped_example()