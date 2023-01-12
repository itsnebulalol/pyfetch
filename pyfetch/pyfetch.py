import os
import sys
import psutil
import subprocess as sp

from .cpuinfo import get_cpu_info
from platform import machine
from time import time
from datetime import datetime
from argparse import Namespace
from pathlib import Path
from shutil import which
from re import fullmatch, sub
from requests import get
from json import loads


class PyFetch:
    def __init__(self, in_package: bool, args: Namespace) -> None:
        self.in_package = in_package
        self.args = args
        
        # Other variables
        self.colors = {
            "black": "\033[30m",
            "red": "\033[31m",
            "green": "\033[32m",
            "orange": "\033[33m",
            "blue": "\033[34m",
            "purple": "\033[35m",
            "cyan": "\033[36m",
            "lightgrey": "\033[37m",
            "darkgrey": "\033[90m",
            "lightred": "\033[91m",
            "lightgreen": "\033[92m",
            "yellow": "\033[93m",
            "lightblue": "\033[94m",
            "pink": "\033[95m",
            "lightcyan": "\033[96m",

            "reset": "\033[0m",
            "bold": "\033[01m",
            "disable": "\033[02m",
            "underline": "\033[04m",
            "reverse": "\033[07m",
            "strikethrough": "\033[09m",
            "invisible": "\033[08m"
        }
        self.units = [
            #(1<<50, ' PB'),
            #(1<<40, ' TB'),
            #(1<<30, ' GB'),
            (1<<20, ' MB'),
            (1<<10, ' KB'),
            (1, (' byte', ' bytes')),
        ]
        self.os = sp.getoutput("uname")

    def get_os_version(self) -> str:
        if self.os == "Darwin":
            return f"{sp.getoutput('sw_vers -productName')} {sp.getoutput('sw_vers -productVersion')} ({sp.getoutput('sw_vers -buildVersion')})"
        elif self.os == "Linux":
            with open("/proc/version", "r") as v:
                kernel = v.read().split(' ')[2]
                
            with open("/etc/os-release", "r") as o:
                l = o.readlines()
                for line in l:
                    if line.startswith("PRETTY_NAME"):
                        distro = line.replace("PRETTY_NAME=\"", "").replace("\"", "").replace("\n", "")
                        break
                
            return f"{distro} (Linux {kernel})"
        else:
            return f"Unknown {self.os}"
    
    def get_model(self) -> str:
        oem_info = [
            "To be filled by O.E.M",
            r"To Be Filled*",
            r"OEM*",
            "Not Applicable",
            "System Product Name",
            "System Version",
            "Undefined",
            "Default string",
            "Not Specified",
            "Type1ProductConfigId",
            "INVALID",
            "All Series",
            "�"
        ]
        model = ""
        
        if self.os == "Linux":
            board_vendor = Path("/sys/devices/virtual/dmi/id/board_vendor")
            board_name = Path("/sys/devices/virtual/dmi/id/board_name")
            if board_vendor.exists() or board_name.exists():
                with open(board_vendor, "r") as v:
                    model = v.read()
                
                with open(board_name, "r") as n:
                    model += f" {n.read()}"
            
            product_name = Path("/sys/devices/virtual/dmi/id/product_name")
            product_version = Path("/sys/devices/virtual/dmi/id/product_version")
            if product_name.exists() or product_version.exists():
                with open(product_name, "r") as n:
                    model = n.read()
                
                with open(product_version, "r") as v:
                    model += f" {v.read()}"
            
            devtree_model = Path("/sys/firmware/devicetree/base/model")
            if devtree_model.exists():
                with open(devtree_model, "r") as d:
                    model = d.read()
            
            sysinfo_model = Path("/tmp/sysinfo/model")
            if sysinfo_model.exists():
                with open(sysinfo_model, "r") as s:
                    model = s.read()
        elif self.os == "Darwin":
            prod_name = sp.getoutput('sw_vers -productName')
            if prod_name == "iPhone OS":
                machine_id = sp.getoutput('uname -m')
            else:
                machine_id = sp.getoutput('sysctl -n hw.model')
                kexts = sp.getoutput("kextstat")
                
                is_hackintosh = True if "FakeSMC" in kexts or "VirtualSMC" in kexts else False
            
            res = get(f"https://di-api.reincubate.com/v1/apple-identifiers/{machine_id}/")

            if res.status_code != 200:
                return machine_id

            j = loads(res.content)
            model = f"{j['product']['sku']}"
            if is_hackintosh:
                model = f"{model} (Hackintosh)"
        
        for info in oem_info:
            model = sub(info, "", model)
        
        if "Standard PC" in model:
            model = f"{model} (KVM)"
            
        if model == "":
            model = "Unknown"
        
        return model.strip()
    
    def in_path(self, cmd) -> bool:
        return which(cmd) is not None
    
    def file_count(self, directory) -> int:
        return len(os.listdir(directory))
    
    def get_packages(self) -> str:
        packages = ""
        
        if self.in_path("pacman"):
            packages += f"{', ' if packages != '' else ''}{self.file_count('/var/lib/pacman/local')} pacman"
        
        if self.in_path("rpm"):
            packages += f"{', ' if packages != '' else ''}{len(sp.getoutput('rpm -qa').splitlines())} rpm"
        
        if self.in_path("emerge"):
            packages += f"{', ' if packages != '' else ''}{self.file_count('/var/db/pkg')} emerge"
        
        if self.in_path("xbps-query"):
            packages += f"{', ' if packages != '' else ''}{len(sp.getoutput('xbps-query -l').splitlines())} xbps"
        
        if self.in_path("dpkg"):
            l = len(sp.getoutput('dpkg -l').splitlines())
            if l != 0:
                packages += f"{', ' if packages != '' else ''}{l} dpkg"
            
        if self.in_path("brew"):
            packages += f"{', ' if packages != '' else ''}{len(sp.getoutput('brew leaves').splitlines())} brew"
            
        if self.in_path("port"):
            packages += f"{', ' if packages != '' else ''}{len(sp.getoutput('port installed').splitlines())} port"
        
        if packages == "":
            return "Unknown"

        return packages
    
    def pretty_size(self, bytes) -> str:
        """
        Get human-readable file sizes.
        Simplified version of https://pypi.python.org/pypi/hurry.filesize/
        Taken from https://stackoverflow.com/a/12912296
        """
        
        for factor, suffix in self.units:
            if bytes >= factor:
                break
        amount = int(bytes / factor)

        if isinstance(suffix, tuple):
            singular, multiple = suffix
            if amount == 1:
                suffix = singular
            else:
                suffix = multiple
                
        return str(amount) + suffix
        
    def get_memory_usage(self) -> str:
        mem_str = ""
        
        mem_str += f"{self.pretty_size(psutil.virtual_memory()[0] - psutil.virtual_memory()[1])} / " # used ram
        mem_str += f"{self.pretty_size(psutil.virtual_memory()[0])} " # total ram
        mem_str += f"({psutil.virtual_memory()[2]}%)" # percentage of ram
        
        return mem_str
    
    def get_uptime(self) -> str:
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        return str(uptime).split(".")[0]

    def get_gpu_info(self) -> str:
        if self.os == "Darwin":
            prod_name = sp.getoutput('sw_vers -productName')
            if prod_name == "iPhone OS":
                pass
            else:
                gpu_info = sp.getoutput("system_profiler SPDisplaysDataType")
                l = gpu_info.splitlines()
                for line in l:
                    if "Chipset Model:" in line:
                        gpu = line.split("Chipset Model: ")[1]
        else:
            lspci = sp.getoutput("lspci")
            l = lspci.splitlines()
            for line in l:
                if "Display" in line or "3D" in line or "VGA" in line:
                    gpu = line.split(": ")[1].split(" (rev")[0]
        
        try:
            if "Intel" in gpu:
                gpu = gpu.replace("Corporation ", "")
            
            return gpu
        except:
            return "Unknown"

    def get_shell(self) -> str:
        shell = os.environ.get('SHELL')
        shell_clean = shell.split("/")[-1]
        
        try:
            if not shell_clean in ("sh", "ash", "dash", "es"):
                if shell_clean == "bash":
                    bash_version = sp.getoutput(f"{shell} --version")
                    version = bash_version.splitlines()[0].split("version ")[1].split(" (")[0]
                elif shell_clean == "zsh":
                    version = sp.getoutput(f"{shell} --version").split(" (")[0]
                else:
                    version = sp.getoutput(f"{shell} --version")
            
            if shell_clean in version:
                return version
            else:
                return f"{shell_clean} {version}"
        except:
            return shell_clean
        

    def add_item(self, icon: str, name: str, content: str, color: str) -> str:
        return f"│ {self.colors[color]}{icon} {self.colors['reset']}{name.ljust(9)}│ {self.colors[color]}{content}{self.colors['reset']}\n"

    def main(self) -> None:
        out = ""
        out += "╭────────────╮\n"
        out += self.add_item("", "user", os.environ.get('USER'), "red")
        out += self.add_item("", "model", self.get_model(), "yellow")
        out += self.add_item("", "os", self.get_os_version(), "green")
        out += self.add_item("", "cpu", f"{get_cpu_info()['brand_raw']} ({machine()})", "cyan")
        out += self.add_item("", "gpu", self.get_gpu_info(), "blue")
        out += self.add_item("", "packages", self.get_packages(), "purple")
        out += self.add_item("", "shell", self.get_shell(), "red")
        out += self.add_item("", "memory", self.get_memory_usage(), "yellow")
        out += self.add_item("", "uptime", self.get_uptime(), "green")
        out += "├────────────┤\n"
        out += self.add_item("", "colors", f"{self.colors['black']}● {self.colors['red']}● {self.colors['yellow']}● {self.colors['green']}● {self.colors['cyan']}● {self.colors['blue']}● {self.colors['purple']}● {self.colors['reset']}●", "reset")
        out += "╰────────────╯"
        
        print(out)
            