import subprocess
import sys
import os

def install_dependencies():
    """
    Install project dependencies from requirements.txt
    """
    try:
        # Upgrade pip to the latest version
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Successfully installed dependencies from requirements.txt")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def download_spacy_model():
    """
    Download the specified SpaCy language model
    """
    try:
        subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_md'])
        print("Successfully downloaded SpaCy model en_core_web_md")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading SpaCy model: {e}")
        sys.exit(1)

def main():
    """
    Main setup function to install dependencies and download models
    """
    install_dependencies()
    download_spacy_model()

if __name__ == '__main__':
    main()
