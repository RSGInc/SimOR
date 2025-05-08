import subprocess

def test_cropped_example():

    subprocess.run(
        [
            "python", "simulation.py",
            "-c", "configs",  # Config directory
            "-d", "model_data/cropped_data",  # Input data directory
            "-o", "outputs/test"  # Output directory
        ], 
        check=True
    )
    
    return True


if __name__ == "__main__":
    test_cropped_example()