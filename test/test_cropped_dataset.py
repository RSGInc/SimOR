import subprocess
import sys

def test_cropped_example():
    try:
        # Command to run the cropped example
        command = [
            "python",  # Path to the Python interpreter
            "simulation.py",  # Script to run
            "-c", "configs",  # Config directory
            "-d", "model_data/cropped_data",  # Input data directory
            "-o", "outputs/test"  # Output directory
        ]

        # Run the command and capture the output
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # Print the output for debugging purposes
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        print("Cropped example ran successfully.")
        return True

    except subprocess.CalledProcessError as e:
        # Print error details if the command fails
        print("Error: Cropped example failed to run.")
        print("Return Code:", e.returncode)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

if __name__ == "__main__":
    success = test_cropped_example()
    sys.exit(0 if success else 1)