from abc import ABC, abstractmethod
from os import urandom
from pathlib import Path
from subprocess import run
from sys import platform
from base64 import urlsafe_b64encode
from typing import Literal
from requests import exceptions, get, post
from twine.commands.upload import upload
from twine.settings import Settings
from twine.exceptions import NonInteractive
from tqdm import tqdm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import ollama

from packer.custom_modules.etf import clear_lines, print_colored_text


def pip_install(packages: list[str], python_exe_path: str | Path | None = None):
    '''
    Install Python packages using pip.

    This function installs a list of Python packages using pip. It can optionally
    use a specific Python executable path for the installation.

    :param packages: A list of package names to install
    :type packages: list[str]
    :param python_exe_path: Path to the Python executable to use for installation.
        If None, the CWD .venv executable is used
    :type python_exe_path: str | Path | None
    '''
    
    if not python_exe_path:
        python_exe_path = ('.venv/Scripts/python.exe'
            if platform == 'win32'
            else '.venv/bin/python')
    run([python_exe_path, '-m', 'pip', 'install', *packages], check=True)

def generate_key_from_password(password: bytes, salt: bytes) -> bytes:
    '''Derives a secure 32-byte key from a user password and salt.'''
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000, # High iteration count makes brute-forcing computationally expensive
    )
    # Fernet keys must be url-safe base64 encoded
    return urlsafe_b64encode(kdf.derive(password))

def is_file_encrypted(file_path: str | Path) -> bool:
    '''
    Check if a file is encrypted by attempting to read its first few bytes.

    This function tries to read the beginning of a file to determine if it is
    likely to be encrypted. It does so by checking for a specific encryption
    signature. The signature is identified by:
    - Reading the first 20 bytes of the file
    - Checking that byte at index 16 is 103 ('g')
    - Checking that bytes at indices 17-19 are 65 ('A')
    :param file_path: The path to the file to check for encryption
    :type file_path: str | Path
    :return: True if the file appears to be encrypted, False otherwise
    :rtype: bool
    '''

    with open(file_path, 'rb') as f:
        # Read the first 20 bytes to check the salt alignment and the 'gAAA' header
        header = f.read(20)
        
    if len(header) < 20:
        return False  # Too small to be our encrypted file
        
    # Index 16 must be 103 (ASCII 'g')
    # Indices 17, 18, 19 must be 65 (ASCII 'A')
    return header[16] == 103 and header[17:20] == b'AAA'

def write_encrypted_file(data: bytes, path: str | Path, password: bytes):
    '''
    Encrypt and write data to a file using a password.

    This function encrypts the provided data using a key derived from the given
    password and writes the encrypted data to the specified file path. The encryption
    uses Fernet symmetric encryption, which is secure and well-suited for this purpose.

    :param data: The plaintext data to encrypt and write to the file
    :type data: bytes
    :param path: The file path where the encrypted data will be written
    :type path: str | Path
    :param password: The password used to derive the encryption key
    :type password: bytes
    '''
    salt = urandom(16)

    # Turn the password + salt into a secure key
    key = generate_key_from_password(password, salt)

    # Encrypt the data
    encrypted_data = Fernet(key).encrypt(data)

    # Write BOTH the salt and the encrypted data to the output file.
    # We put the 16-byte salt at the very beginning so we can grab it during decryption.
    with open(path, 'wb') as f:
        f.write(salt)
        f.write(encrypted_data)
    

def read_encrypted_file(file_path: str | Path, password: bytes) -> str:
    # Read the combined file (encryption and actual content)
    with open(file_path, 'rb') as f:
        combined_data = f.read()

    # Extract the 16-byte salt from the front, and the rest is the ciphertext
    extracted_salt = combined_data[:16]
    extracted_ciphertext = combined_data[16:]

    # Re-derive the exact same key using the password and the extracted salt
    decryption_key = generate_key_from_password(password, extracted_salt)

    # Decrypt back to original data
    decrypted_data = Fernet(decryption_key).decrypt(extracted_ciphertext)

    return decrypted_data.decode()

def model_pull_progress(model_name: str):
    for progress in ollama.pull(model_name, stream=True):
        yield {
            'total': progress.total,
            'completed': progress.completed,
            'status': progress.status,
        }

class ProgressRenderer(ABC):
    @abstractmethod
    def start(self, total: int) -> None:
        pass

    @abstractmethod
    def update(self, completed: int, status: str | None) -> None:
        pass

    @abstractmethod
    def finish(self) -> None:
        pass

class TqdmProgressRenderer(ProgressRenderer):
    def __init__(self):
        self.bar = None
        self.lines = 0

    def start(self, total):
        if self.bar:
            self.bar.close()
        self.bar = tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024)
        self.lines += 1

    def update(self, completed, status):
        self.bar.n = completed
        self.bar.set_description(status)
        self.bar.refresh()

    def finish(self):
        self.bar.close()
        clear_lines(self.lines)
        print_colored_text('Successfully installed!', [0, 255, 0])

def track_model_pull(model_name: str, renderer: ProgressRenderer):
    stream = model_pull_progress(model_name)

    first = next(stream)
    while not first['total']:
        first = next(stream)
    total = first['total']
    renderer.start(total)

    for progress in stream:
        if progress['completed']:
            if progress['total'] == total:
                renderer.update(progress['completed'], progress['status'])
            else:
                total = progress['total']
                renderer.start(total)

    renderer.finish()

def upload_package(output_dir: str | Path = 'dist', repository: str = 'pypi', api_token: str | None = None) -> str | None:
    '''
    Uploads generated distribution files to PyPI or TestPyPI.
    
    :param output_dir: Directory where the built distributions are located
    :type output_dir: str | Path
    :param repository: 'pypi' or 'testpypi'
    :type repository: str
    :param api_token: String starting with 'pypi-'
    :type api_token: str
    :return: None if upload is successful, or error message if it fails
    :rtype: str | None
    '''

    dist_files = [str(p) for p in Path(output_dir).glob('*') if p.suffix in ('.whl', '.gz')]
    
    if not dist_files:
        return 'No distribution files found to upload.'

    # Set repository URL target
    repo_url = 'https://upload.pypi.org/legacy/' if repository == 'pypi' else 'https://test.pypi.org/legacy/'

    # Configure twine upload settings
    settings = Settings(
        repository_url=repo_url,
        username='__token__',
        password=api_token,  # Twine will check ~/.pypirc or environment variables if None
        non_interactive=True,
        verbose=True
    )

    try:
        upload(settings, dist_files)
    except NonInteractive as e:
        return str(e)
    except exceptions.HTTPError as e:
        return e.response.text


def find_environments(github_repo_token: str, github_repo_url: str, run_id: int, environment_name: str = 'pypi-production') -> int:
    '''
    sends a request to the GitHub API to retrieve the list of pending deployments for a specific workflow run.
    
    :param github_repo_token: The GitHub token used to authenticate with the GitHub API
    :type github_repo_token: str
    :param github_repo_url: The GitHub repository URL in the format "owner/repo"
    :type github_repo_url: str
    :param run_id: The ID of the workflow run to retrieve pending deployments for
    :type run_id: int
    :param environment_name: The name of the environment to retrieve the ID for (default is "pypi-production")
    :type environment_name: str

    :return: The ID of the environment with the provided environment name
    :rtype: int

    :raises requests.exceptions.HTTPError: If the request to the GitHub API fails
    '''

    response = get(
        f'https://api.github.com/repos/{github_repo_url}'
        f'/actions/runs/{run_id}/pending_deployments',
        headers={
            'Authorization': f'Bearer {github_repo_token}',
            'Accept': 'application/vnd.github+json',
        },
    )
    response.raise_for_status()

    deployments = response.json()

    environment = next(
        deployment
        for deployment in deployments
        if deployment['environment']['name'] == environment_name
    )

    return environment['environment']['id']

def process_deployed_environments(github_repo_token: str, github_repo_url: str, run_id: int, environment_id: int, state: Literal['approved', 'rejected'] = 'approved', comment: str = 'Approved through Packer'):
    '''
    sends a request to the GitHub API to approve or reject a specific workflow run for a specific environment.
    
    :param github_repo_token: The GitHub token used to authenticate with the GitHub API
    :type github_repo_token: str
    :param github_repo_url: The GitHub repository URL in the format "owner/repo"
    :type github_repo_url: str
    :param run_id: The ID of the workflow run to approve or reject
    :type run_id: int
    :param environment_id: The ID of the environment to approve or reject the workflow run for
    :type environment_id: int

    :raises requests.exceptions.HTTPError: If the request to the GitHub API fails
    '''

    post(
        f'https://api.github.com/repos/{github_repo_url}'
        f'/actions/runs/{run_id}/pending_deployments',
        headers={
            'Authorization': f'Bearer {github_repo_token}',
            'Accept': 'application/vnd.github+json',
        },
        json={
            'environment_ids': [environment_id],
            'state': state,
            'comment': comment,
        },
    ).raise_for_status()