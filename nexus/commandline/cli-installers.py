import subprocess
import platform
import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class InstallMethod(Enum):
    """Installation methods for different CLIs"""
    CURL_BASH = "curl_bash"
    WGET_BASH = "wget_bash"
    PIP = "pip"
    NPM = "npm"
    BREW = "brew"
    APT = "apt"
    YUM = "yum"
    CHOCO = "choco"
    WINGET = "winget"
    SCRIPT = "script"
    BINARY = "binary"


@dataclass
class CLITool:
    """Represents a CLI tool with installation instructions"""
    name: str
    install_method: InstallMethod
    install_command: str
    verify_command: str
    windows_command: Optional[str] = None
    macos_command: Optional[str] = None
    linux_command: Optional[str] = None


class CLIInstaller:
    """Silent installer for top 50 cloud and DevOps CLI tools"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.system = platform.system().lower()
        self.installed_tools = []
        self.failed_tools = []
        
        # Define the top 50 CLI tools
        self.cli_tools: Dict[str, CLITool] = {
            # Cloud Provider CLIs
            "aws": CLITool(
                "AWS CLI",
                InstallMethod.SCRIPT,
                "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip -q awscliv2.zip && sudo ./aws/install",
                "aws --version",
                windows_command="msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi /qn",
                macos_command="curl 'https://awscli.amazonaws.com/AWSCLIV2.pkg' -o 'AWSCLIV2.pkg' && sudo installer -pkg AWSCLIV2.pkg -target /"
            ),
            "azure": CLITool(
                "Azure CLI",
                InstallMethod.CURL_BASH,
                "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash",
                "az --version",
                windows_command="powershell -Command \"Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'\"",
                macos_command="brew install azure-cli"
            ),
            "gcloud": CLITool(
                "Google Cloud CLI",
                InstallMethod.SCRIPT,
                "curl https://sdk.cloud.google.com | bash && exec -l $SHELL",
                "gcloud --version",
                windows_command="powershell -Command \"(New-Object Net.WebClient).DownloadFile('https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe', '.\\GoogleCloudSDKInstaller.exe'); Start-Process .\\GoogleCloudSDKInstaller.exe -ArgumentList '/S' -Wait\"",
                macos_command="curl https://sdk.cloud.google.com | bash"
            ),
            "oci": CLITool(
                "Oracle Cloud CLI",
                InstallMethod.CURL_BASH,
                "bash -c \"$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)\" -- --accept-all-defaults",
                "oci --version",
                windows_command="powershell -Command \"Invoke-WebRequest https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.ps1 -OutFile install.ps1; .\\install.ps1 -AcceptAllDefaults\"",
            ),
            "ibmcloud": CLITool(
                "IBM Cloud CLI",
                InstallMethod.CURL_BASH,
                "curl -fsSL https://clis.cloud.ibm.com/install/linux | sh",
                "ibmcloud --version",
                windows_command="powershell -Command \"iex(New-Object Net.WebClient).DownloadString('https://clis.cloud.ibm.com/install/powershell')\"",
                macos_command="curl -fsSL https://clis.cloud.ibm.com/install/osx | sh"
            ),
            "doctl": CLITool(
                "DigitalOcean CLI",
                InstallMethod.SCRIPT,
                "cd ~ && wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz && tar xf ~/doctl-1.94.0-linux-amd64.tar.gz && sudo mv ~/doctl /usr/local/bin",
                "doctl version",
                macos_command="brew install doctl"
            ),
            "linode-cli": CLITool(
                "Linode CLI",
                InstallMethod.PIP,
                "pip3 install linode-cli --quiet",
                "linode-cli --version"
            ),
            "vultr-cli": CLITool(
                "Vultr CLI",
                InstallMethod.SCRIPT,
                "wget -O /usr/local/bin/vultr-cli https://github.com/vultr/vultr-cli/releases/latest/download/vultr-cli_linux_amd64 && chmod +x /usr/local/bin/vultr-cli",
                "vultr-cli version",
                macos_command="brew tap vultr/vultr-cli && brew install vultr-cli"
            ),
            
            # Container & Orchestration
            "kubectl": CLITool(
                "Kubernetes CLI",
                InstallMethod.SCRIPT,
                "curl -LO \"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\" && sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl",
                "kubectl version --client",
                windows_command="curl -LO https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe",
                macos_command="brew install kubectl"
            ),
            "helm": CLITool(
                "Helm",
                InstallMethod.CURL_BASH,
                "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
                "helm version",
                macos_command="brew install helm"
            ),
            "docker": CLITool(
                "Docker CLI",
                InstallMethod.SCRIPT,
                "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh",
                "docker --version",
                macos_command="brew install docker"
            ),
            "k9s": CLITool(
                "K9s",
                InstallMethod.SCRIPT,
                "curl -sS https://webinstall.dev/k9s | bash",
                "k9s version",
                macos_command="brew install k9s"
            ),
            "kind": CLITool(
                "Kind",
                InstallMethod.SCRIPT,
                "curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind",
                "kind version",
                macos_command="brew install kind"
            ),
            "minikube": CLITool(
                "Minikube",
                InstallMethod.SCRIPT,
                "curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && sudo install minikube-linux-amd64 /usr/local/bin/minikube",
                "minikube version",
                macos_command="brew install minikube"
            ),
            
            # Infrastructure as Code
            "terraform": CLITool(
                "Terraform",
                InstallMethod.SCRIPT,
                "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && echo \"deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main\" | sudo tee /etc/apt/sources.list.d/hashicorp.list && sudo apt update && sudo apt install -y terraform",
                "terraform --version",
                macos_command="brew tap hashicorp/tap && brew install hashicorp/tap/terraform"
            ),
            "pulumi": CLITool(
                "Pulumi",
                InstallMethod.CURL_BASH,
                "curl -fsSL https://get.pulumi.com | sh",
                "pulumi version",
                macos_command="brew install pulumi"
            ),
            "ansible": CLITool(
                "Ansible",
                InstallMethod.PIP,
                "pip3 install ansible --quiet",
                "ansible --version"
            ),
            "packer": CLITool(
                "Packer",
                InstallMethod.SCRIPT,
                "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && sudo apt install -y packer",
                "packer version",
                macos_command="brew install packer"
            ),
            "vagrant": CLITool(
                "Vagrant",
                InstallMethod.SCRIPT,
                "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && sudo apt install -y vagrant",
                "vagrant --version",
                macos_command="brew install vagrant"
            ),
            
            # CI/CD & DevOps
            "gh": CLITool(
                "GitHub CLI",
                InstallMethod.SCRIPT,
                "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt update && sudo apt install -y gh",
                "gh --version",
                macos_command="brew install gh"
            ),
            "gitlab-cli": CLITool(
                "GitLab CLI",
                InstallMethod.SCRIPT,
                "curl -s https://gitlab.com/gitlab-org/cli/-/releases/permalink/latest/downloads/glab_linux_amd64.tar.gz | tar xz && sudo mv bin/glab /usr/local/bin/",
                "glab version",
                macos_command="brew install glab"
            ),
            "jenkins-cli": CLITool(
                "Jenkins CLI",
                InstallMethod.SCRIPT,
                "wget http://localhost:8080/jnlpJars/jenkins-cli.jar -O /usr/local/bin/jenkins-cli.jar",
                "java -jar /usr/local/bin/jenkins-cli.jar -s http://localhost:8080/ version"
            ),
            "circleci": CLITool(
                "CircleCI CLI",
                InstallMethod.CURL_BASH,
                "curl -fLSs https://raw.githubusercontent.com/CircleCI-Public/circleci-cli/master/install.sh | sudo bash",
                "circleci version",
                macos_command="brew install circleci"
            ),
            "travis": CLITool(
                "Travis CI CLI",
                InstallMethod.SCRIPT,
                "gem install travis --no-document",
                "travis version"
            ),
            
            # Monitoring & Observability
            "datadog": CLITool(
                "Datadog CLI",
                InstallMethod.PIP,
                "pip3 install datadog --quiet",
                "dog --version"
            ),
            "newrelic": CLITool(
                "New Relic CLI",
                InstallMethod.SCRIPT,
                "curl -Ls https://download.newrelic.com/install/newrelic-cli/scripts/install.sh | bash",
                "newrelic version",
                macos_command="brew install newrelic-cli"
            ),
            "prometheus": CLITool(
                "Prometheus CLI",
                InstallMethod.SCRIPT,
                "wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz && tar xvf prometheus-2.45.0.linux-amd64.tar.gz && sudo mv prometheus-2.45.0.linux-amd64/promtool /usr/local/bin/",
                "promtool --version",
                macos_command="brew install prometheus"
            ),
            
            # Database CLIs
            "mysql": CLITool(
                "MySQL CLI",
                InstallMethod.APT,
                "sudo apt install -y mysql-client",
                "mysql --version",
                macos_command="brew install mysql-client"
            ),
            "postgresql": CLITool(
                "PostgreSQL CLI",
                InstallMethod.APT,
                "sudo apt install -y postgresql-client",
                "psql --version",
                macos_command="brew install postgresql"
            ),
            "redis-cli": CLITool(
                "Redis CLI",
                InstallMethod.APT,
                "sudo apt install -y redis-tools",
                "redis-cli --version",
                macos_command="brew install redis"
            ),
            "mongodb": CLITool(
                "MongoDB CLI",
                InstallMethod.SCRIPT,
                "wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add - && echo \"deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse\" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list && sudo apt update && sudo apt install -y mongodb-mongosh",
                "mongosh --version",
                macos_command="brew install mongosh"
            ),
            
            # Serverless & Functions
            "serverless": CLITool(
                "Serverless Framework",
                InstallMethod.NPM,
                "npm install -g serverless",
                "serverless --version"
            ),
            "sam": CLITool(
                "AWS SAM CLI",
                InstallMethod.PIP,
                "pip3 install aws-sam-cli --quiet",
                "sam --version"
            ),
            "functions": CLITool(
                "Azure Functions CLI",
                InstallMethod.NPM,
                "npm install -g azure-functions-core-tools@4",
                "func --version"
            ),
            
            # Package Managers & Build Tools
            "npm": CLITool(
                "NPM",
                InstallMethod.APT,
                "sudo apt install -y npm",
                "npm --version",
                macos_command="brew install node"
            ),
            "yarn": CLITool(
                "Yarn",
                InstallMethod.NPM,
                "npm install -g yarn",
                "yarn --version",
                macos_command="brew install yarn"
            ),
            "pip": CLITool(
                "Pip",
                InstallMethod.APT,
                "sudo apt install -y python3-pip",
                "pip3 --version",
                macos_command="brew install python"
            ),
            "maven": CLITool(
                "Maven",
                InstallMethod.APT,
                "sudo apt install -y maven",
                "mvn --version",
                macos_command="brew install maven"
            ),
            "gradle": CLITool(
                "Gradle",
                InstallMethod.SCRIPT,
                "wget https://services.gradle.org/distributions/gradle-8.3-bin.zip && unzip -q gradle-8.3-bin.zip && sudo mv gradle-8.3 /opt/gradle && sudo ln -s /opt/gradle/bin/gradle /usr/local/bin/gradle",
                "gradle --version",
                macos_command="brew install gradle"
            ),
            
            # Security & Secrets Management
            "vault": CLITool(
                "HashiCorp Vault",
                InstallMethod.SCRIPT,
                "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && sudo apt install -y vault",
                "vault version",
                macos_command="brew install vault"
            ),
            "consul": CLITool(
                "Consul",
                InstallMethod.SCRIPT,
                "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && sudo apt install -y consul",
                "consul version",
                macos_command="brew install consul"
            ),
            "sops": CLITool(
                "SOPS",
                InstallMethod.SCRIPT,
                "wget https://github.com/mozilla/sops/releases/download/v3.7.3/sops-v3.7.3.linux -O sops && chmod +x sops && sudo mv sops /usr/local/bin/",
                "sops --version",
                macos_command="brew install sops"
            ),
            
            # Service Mesh & Networking
            "istioctl": CLITool(
                "Istio CLI",
                InstallMethod.CURL_BASH,
                "curl -L https://istio.io/downloadIstio | sh - && sudo mv istio-*/bin/istioctl /usr/local/bin/",
                "istioctl version",
                macos_command="brew install istioctl"
            ),
            "linkerd": CLITool(
                "Linkerd CLI",
                InstallMethod.CURL_BASH,
                "curl -fsL https://run.linkerd.io/install | sh",
                "linkerd version",
                macos_command="brew install linkerd"
            ),
            
            # API & Testing
            "curl": CLITool(
                "cURL",
                InstallMethod.APT,
                "sudo apt install -y curl",
                "curl --version",
                macos_command="brew install curl"
            ),
            "httpie": CLITool(
                "HTTPie",
                InstallMethod.PIP,
                "pip3 install httpie --quiet",
                "http --version"
            ),
            "jq": CLITool(
                "jq",
                InstallMethod.APT,
                "sudo apt install -y jq",
                "jq --version",
                macos_command="brew install jq"
            ),
            "yq": CLITool(
                "yq",
                InstallMethod.SCRIPT,
                "wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq && chmod +x /usr/local/bin/yq",
                "yq --version",
                macos_command="brew install yq"
            ),
            
            # Additional Tools
            "git": CLITool(
                "Git",
                InstallMethod.APT,
                "sudo apt install -y git",
                "git --version",
                macos_command="brew install git"
            ),
            "rsync": CLITool(
                "Rsync",
                InstallMethod.APT,
                "sudo apt install -y rsync",
                "rsync --version",
                macos_command="brew install rsync"
            ),
            "ssh": CLITool(
                "OpenSSH",
                InstallMethod.APT,
                "sudo apt install -y openssh-client",
                "ssh -V",
                macos_command="# SSH pre-installed on macOS"
            ),
        }
    
    def _run_command(self, command: str, shell: bool = True) -> tuple:
        """Execute a command silently and return success status and output"""
        try:
            result = subprocess.run(
                command,
                shell=shell,
                stdout=subprocess.PIPE if not self.verbose else None,
                stderr=subprocess.PIPE if not self.verbose else None,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout if result.stdout else ""
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, str(e)
    
    def _is_installed(self, verify_command: str) -> bool:
        """Check if a tool is already installed"""
        success, _ = self._run_command(verify_command)
        return success
    
    def _get_platform_command(self, tool: CLITool) -> str:
        """Get the appropriate installation command for the current platform"""
        if self.system == "darwin" and tool.macos_command:
            return tool.macos_command
        elif self.system == "windows" and tool.windows_command:
            return tool.windows_command
        elif self.system == "linux" and tool.linux_command:
            return tool.linux_command
        return tool.install_command
    
    def install_tool(self, tool_key: str) -> bool:
        """Install a single CLI tool"""
        if tool_key not in self.cli_tools:
            print(f"Unknown tool: {tool_key}")
            return False
        
        tool = self.cli_tools[tool_key]
        
        # Check if already installed
        if self._is_installed(tool.verify_command):
            if self.verbose:
                print(f"✓ {tool.name} is already installed")
            self.installed_tools.append(tool_key)
            return True
        
        if self.verbose:
            print(f"Installing {tool.name}...")
        
        # Get platform-specific command
        install_cmd = self._get_platform_command(tool)
        
        # Run installation
        success, output = self._run_command(install_cmd)
        
        if success:
            # Verify installation
            if self._is_installed(tool.verify_command):
                if self.verbose:
                    print(f"✓ {tool.name} installed successfully")
                self.installed_tools.append(tool_key)
                return True
        
        if self.verbose:
            print(f"✗ Failed to install {tool.name}")
            if output:
                print(f"  Error: {output}")
        
        self.failed_tools.append(tool_key)
        return False
    
    def install_all(self, tools: Optional[List[str]] = None):
        """Install all CLI tools or a specific list of tools"""
        tools_to_install = tools if tools else list(self.cli_tools.keys())
        
        print(f"Starting installation of {len(tools_to_install)} CLI tools...")
        print("=" * 60)
        
        for tool_key in tools_to_install:
            self.install_tool(tool_key)
        
        print("=" * 60)
        print(f"\nInstallation Summary:")
        print(f"  Successfully installed: {len(self.installed_tools)}")
        print(f"  Failed: {len(self.failed_tools)}")
        
        if self.failed_tools and self.verbose:
            print(f"\nFailed tools: {', '.join(self.failed_tools)}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of all available tools"""
        return list(self.cli_tools.keys())
    
    def get_tool_info(self, tool_key: str) -> Optional[CLITool]:
        """Get information about a specific tool"""
        return self.cli_tools.get(tool_key)


# Example usage
if __name__ == "__main__":
    # Create installer instance with verbose output
    installer = CLIInstaller(verbose=True)
    
    # Install all tools
    installer.install_all()
    
    # Or install specific tools
    # installer.install_all(["aws", "azure", "gcloud", "kubectl", "terraform"])
    
    # Get list of available tools
    # print("\nAvailable tools:")
    # for tool in installer.get_available_tools():
    #     print(f"  - {tool}")