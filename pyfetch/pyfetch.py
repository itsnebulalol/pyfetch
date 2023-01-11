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
    
    def in_path(self, cmd) -> bool:
        return which(cmd) is not None
    
    def file_count(self, directory) -> int:
        _, _, files = next(os.walk(directory))
        return len(files)
    
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

    def add_item(self, icon: str, name: str, content: str, color: str) -> str:
        return f"│ {self.colors[color]}{icon} {self.colors['reset']}{name.ljust(9)}│ {self.colors[color]}{content}{self.colors['reset']}\n"

    def main(self) -> None:
        out = ""
        out += "╭────────────╮\n"
        out += self.add_item("", "user", os.environ.get('USER'), "red")
        out += self.add_item("", "os", self.get_os_version(), "yellow")
        out += self.add_item("", "packages", self.get_packages(), "green")
        out += self.add_item("", "shell", os.environ.get('SHELL').split("/")[-1], "cyan")
        out += self.add_item("", "memory", self.get_memory_usage(), "blue")
        out += self.add_item("", "uptime", self.get_uptime(), "purple")
        out += self.add_item("", "cpu", f"{get_cpu_info()['brand_raw']} ({machine()})", "red")
        out += "├────────────┤\n"
        out += self.add_item("", "colors", f"{self.colors['black']}● {self.colors['red']}● {self.colors['yellow']}● {self.colors['green']}● {self.colors['cyan']}● {self.colors['blue']}● {self.colors['purple']}● {self.colors['reset']}●", "reset")
        out += "╰────────────╯"
        
        print(out)
            