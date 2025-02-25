import tarfile
import os

def extract_tarball(tarball):
    print(f"Extracting to: {os.getcwd()}")
    with tarfile.open(tarball, 'r:bz2') as tar:
        tar.extractall('./')
    print("Contents of the directory after extraction:")
    for item in os.listdir('./'):
        print(item)