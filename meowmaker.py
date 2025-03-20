import os
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set safe directory for git to prevent dubious ownership error
subprocess.run(["git", "config", "--global", "--add", "safe.directory", "/github/workspace"])

# Now you can proceed with your Git operations safely
# Example of adding files to Git
try:
    result = subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd="/github/workspace")
    if result.returncode != 0:
        raise RuntimeError(f"Failed to add files: {result.stderr}")
except Exception as e:
    print("Error occurred:", e)

def print_directory_structure(start_path, level=0, max_depth=1):
    """Recursively prints the directory structure, limited to max_depth."""
    if level > max_depth:  # Stop recursion if max depth is exceeded
        return
    with os.scandir(start_path) as entries:
        for entry in entries:
            print('    ' * level + '|-- ' + entry.name)
            if entry.is_dir():
                print_directory_structure(entry.path, level + 1, max_depth)

def log_files_in_directory(directory):
    """Logs all files in the specified directory."""
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            log_files_in_directory(item_path)
        else:
            logger.info(f"  - {item}, Size: {os.path.getsize(item_path)} bytes")

def git_commit_push(output_folder, commit_message, branch_name):
    """Stages and pushes changes to the repository."""
    # Change to the working directory for git
    os.chdir("/github/workspace")
    # Stage output folder
    subprocess.run(["git", "add", '.'], check=True)

    # Commit changes
    try:
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
    except subprocess.CalledProcessError as e:
        logger.info("No changes to commit.")
        return

    # Push changes back to the repository, specifying the branch
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    subprocess.run(["git", "push", f"https://x-access-token:{github_token}@github.com/{repo}.git", f"HEAD:{branch_name}"], check=True)
    
def main():
    """Execute the Tera Processing Workflow."""
    try:
        # Change working directory to /workspace
        os.chdir("/github/workspace")

        # Access inputs from environment variables
        input_folder = os.environ.get('INPUT_INPUT_FOLDER', 'templates')  # Mapped from action.yml
        output_folder = os.environ.get('INPUT_OUTPUT_FOLDER', 'output')  # Mapped from action.yml
        git_username = os.environ.get('INPUT_GIT_USERNAME', 'github-actions[bot]')  # Mapped from action.yml
        git_email = os.environ.get('INPUT_GIT_EMAIL', 'github-actions[bot]@users.noreply.github.com')  # Mapped from action.yml
        commit_message = os.environ.get('INPUT_COMMIT_MESSAGE', '🐱 - Generated via Meow Maker')  # Mapped from action.yml
        skip_ci = os.environ.get('INPUT_SKIP_CI', 'yes')  # Mapped from action.yml
        branch_name = os.getenv("INPUT_BRANCH_NAME") 
        root_dir = '/github/workspace/'

        subprocess.run(["git", "config", "--global", "--add", "user.email", git_email])
        subprocess.run(["git", "config", "--global", "--add", "user.name", git_username])

        # Stripping leading and trailing slashes
        input_folder = input_folder.strip('/')
        output_folder = output_folder.strip('/')

        # Log the resolved input/output paths
        logger.info(f"SRCFOLDER (Input): {input_folder}")
        logger.info(f"DSTFOLDER (Output): {output_folder}")
        logger.info(f"Git Username: {git_username}")
        logger.info(f"Git Email: {git_email}")
        logger.info(f"Commit Message: {commit_message}")
        logger.info(f"Skip CI: {skip_ci}")

        # Define the full path for the output folder
        output_path = os.path.join(root_dir, output_folder)

        # Create the output folder if it doesn't exist
        os.makedirs(output_path, exist_ok=True)

        # Get the current working directory
        current_directory = os.getcwd()
        contents = os.listdir(current_directory)

        # Check if the input folder exists
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Error: Input directory '{input_folder}' does not exist.")

        logger.info("Logging contents of the input folder:")
        for filename in os.listdir(input_folder):
            logger.info(f"  - {filename}")

        # Get the list of Tera files in the input folder
        tera_files = [f for f in os.listdir(input_folder) if f.endswith('.tera')]

        # Process each Tera file
        for tera_file in tera_files:
            working_file_path = os.path.join(root_dir, input_folder, tera_file)
            result = subprocess.run(["/app/whiskers", working_file_path], capture_output=True, text=True, cwd=output_path)

            logger.info(f"Processing '{working_file_path}': {result.stdout}")
            if result.returncode != 0:
                logger.error(f"Whiskers execution failed for '{working_file_path}': {result.stderr}")
                continue

            logger.info(f"Whiskers executed successfully for '{working_file_path}'")

        logger.info("Generated files in output directory:")
        log_files_in_directory(output_path)
        
        # Commit and push changes to GitHub based on SKIP_CI
        if skip_ci.lower() == 'yes':
            commit_message += " [no ci]"

        # After all processing is done:
        git_commit_push(output_folder, commit_message, branch_name)

    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")

if __name__ == "__main__":
    main()