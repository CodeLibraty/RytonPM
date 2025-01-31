import os
import sys
import json
import shutil
import requests
import subprocess
from pathlib import Path

class RytonPackageManager:
    def __init__(self, project_path: str):
        # Сохраняем путь к бинарникам до смены директории
        self.rpm_root = Path(sys.argv[0]).resolve().parent
        self.bin_path = self.rpm_root / 'bin'
        self.zigmod_bin = self.bin_path / ('zigmod.exe' if os.name == 'nt' else 'zigmod')

        # Теперь можно безопасно переходить в директорию проекта
        self.project_path = Path(project_path)
        self.modules_path = self.project_path / 'modules'
        self.ryton_path = self.modules_path / 'ryton'
        self.python_path = self.modules_path / 'python' 
        self.zig_path = self.modules_path / 'zig'

        for path in [self.modules_path, self.ryton_path, 
                    self.python_path, self.zig_path]:
            path.mkdir(exist_ok=True)

    def install(self, package_name: str, source: str = 'ryton'):
        if source == 'ryton':
            return self._install_ryton_package(package_name)
        elif source == 'python':
            return self._install_python_package(package_name)
        elif source == 'zig':
            return self._install_zig_package(package_name)
        else:
            print(f"Error: Unknown source {source}")
            return False

    def _install_ryton_package(self, package_name: str) -> bool:
        try:
            registry_url = "https://raw.githubusercontent.com/CodeLibraty/RytonRegistry/main/packages.json"
            response = requests.get(registry_url)
            
            # Remove any comments or extra whitespace
            json_text = '\n'.join(line for line in response.text.split('\n') 
                                if not line.strip().startswith('//'))
            
            packages = json.loads(json_text)
            
            if package_name not in packages:
                print(f"Package {package_name} not found in Ryton registry")
                return False
                
            package_info = packages[package_name]
            repo_url = package_info['repository']
            author = package_info['author']
            
            print(f"Installing {package_name} by {author}")
            
            target_dir = self.ryton_path / package_name
            subprocess.run(['git', 'clone', repo_url, str(target_dir)], check=True)
            
            self.update_dependencies(package_name, 'ryton')
            return True
            
        except Exception as e:
            print(f"Error installing Ryton package: {e}")
            return False

    def _install_python_package(self, package_name: str) -> bool:
        try:
            pypi_url = f'https://pypi.org/pypi/{package_name}/json'
            response = requests.get(pypi_url)
            response.raise_for_status()
            
            package_data = response.json()
            # Берем wheel или source distribution
            for url_data in package_data['urls']:
                if url_data['packagetype'] in ['bdist_wheel', 'sdist']:
                    download_url = url_data['url']
                    break
                    
            target_dir = self.python_path / package_name
            response = requests.get(download_url)
            
            # Сохраняем архив
            archive_path = self.modules_path / f'temp.{url_data["packagetype"]}'
            with open(archive_path, 'wb') as f:
                f.write(response.content)
                
            # Распаковываем
            if url_data['packagetype'] == 'bdist_wheel':
                shutil.unpack_archive(archive_path, target_dir, format='zip')
            else:
                shutil.unpack_archive(archive_path, target_dir, format='gztar')
                
            archive_path.unlink()
            self.update_dependencies(package_name, 'python')
            return True

        except Exception as e:
            print(f"Error installing Python package: {e}")
            return False

    def install_from_github(self, repo_url: str, source_type: str = 'ryton'):
        """
        Установка модуля напрямую с GitHub
        repo_url: username/repository или полный URL
        source_type: тип модуля (ryton/python/zig)
        """
        try:
            if 'github.com' not in repo_url:
                repo_url = f'https://github.com/{repo_url}'
                
            package_name = repo_url.split('/')[-1]
            target_dir = getattr(self, f"{source_type}_path") / package_name
            
            subprocess.run(['git', 'clone', repo_url, str(target_dir)], check=True)
            self.update_dependencies(f"github:{repo_url}", source_type)
            return True
            
        except Exception as e:
            print(f"Error installing from GitHub: {e}")
            return False

    def _install_zig_package(self, package_name: str) -> bool:
        try:
            # Map of known Zig packages to their GitHub repos
            ZIG_PACKAGES = {
                'mach': 'hexops/mach',
                'zap': 'zigzap/zap',
                'args': 'MasterQ32/zig-args',
                'network': 'MasterQ32/zig-network',
                'opengl': 'MasterQ32/zig-opengl',
                'gamedev': 'michal-z/zig-gamedev',
                'json': 'getty-zig/json'
            }

            if package_name not in ZIG_PACKAGES:
                print(f"Package {package_name} not found in Zig packages list")
                return False
                
            repo = ZIG_PACKAGES[package_name]
            repo_url = f"https://github.com/{repo}"
            target_dir = self.zig_path / package_name
            
            subprocess.run(['git', 'clone', repo_url, str(target_dir)], check=True)
            self.update_dependencies(package_name, 'zig')
            return True
            
        except Exception as e:
            print(f"Error installing Zig package: {e}")
            return False

    def download_and_extract(self, url: str, target_dir: Path):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        archive_path = self.modules_path / 'temp.tar.gz'
        with open(archive_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        shutil.unpack_archive(archive_path, target_dir)
        archive_path.unlink()

    def update_dependencies(self, package_name: str, source: str):
        config_path = self.project_path / 'ryton.toml'
        
        config = {'dependencies': {}} if not config_path.exists() else json.loads(config_path.read_text())
        
        if source not in config['dependencies']:
            config['dependencies'][source] = []
            
        if package_name not in config['dependencies'][source]:
            config['dependencies'][source].append(package_name)
            
        config_path.write_text(json.dumps(config, indent=4))

    def remove(self, package_name: str, source: str = 'ryton'):
        target_dir = getattr(self, f"{source}_path") / package_name
        
        if not target_dir.exists():
            print(f"Package {package_name} not installed")
            return False
            
        shutil.rmtree(target_dir)
        self.remove_from_dependencies(package_name, source)
        return True

    def remove_from_dependencies(self, package_name: str, source: str):
        config_path = self.project_path / 'ryton.toml'
        if not config_path.exists():
            return
            
        config = json.loads(config_path.read_text())
        if source in config['dependencies']:
            if package_name in config['dependencies'][source]:
                config['dependencies'][source].remove(package_name)
                
        config_path.write_text(json.dumps(config, indent=4))

    def list_packages(self, source: str = None):
        sources = [source] if source else ['ryton', 'python', 'zig']
        
        for src in sources:
            path = getattr(self, f"{src}_path")
            if path.exists():
                packages = [d.name for d in path.iterdir() if d.is_dir()]
                if packages:
                    print(f"\n{src.capitalize()} packages:")
                    for pkg in packages:
                        print(f"  - {pkg}")
