import subprocess
import sys

def install_dependencies():
    # Install requirements
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Download SpaCy model
    subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_md'])

if __name__ == '__main__':
    install_dependencies()
