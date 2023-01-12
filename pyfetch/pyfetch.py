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
                
                # iPads -- there are too many iPads and I'm not putting them all
                if machine_id == "iPad1,1":
                    model = "iPad"
                elif fullmatch(r"iPad2,[1-4]", machine_id):
                    model = "iPad 2"
                elif fullmatch(r"iPad3,[1-3]", machine_id):
                    model = "iPad 3"
                elif fullmatch(r"iPad3,[4-6]", machine_id):
                    model = "iPad 4"
                elif fullmatch(r"iPad6,1[12]", machine_id):
                    model = "iPad 5"
                elif fullmatch(r"iPad7,[5-6]", machine_id):
                    model = "iPad 6"
                elif fullmatch(r"iPad7,1[12]", machine_id):
                    model = "iPad 7"
                elif fullmatch(r"iPad11,[67]", machine_id):
                    model = "iPad 8"
                elif fullmatch(r"iPad4,[1-3]", machine_id):
                    model = "iPad Air"
                elif fullmatch(r"iPad5,[3-4]", machine_id):
                    model = "iPad Air 2"
                elif fullmatch(r"iPad11,[3-4]", machine_id):
                    model = "iPad Air 3"
                elif fullmatch(r"iPad13,[1-2]", machine_id):
                    model = "iPad Air 4"
                elif fullmatch(r"iPad6,[7-8]", machine_id):
                    model = "iPad Pro (12.9 inch)"
                elif fullmatch(r"iPad6,[3-4]", machine_id):
                    model = "iPad Pro (9.7 inch)"
                elif fullmatch(r"iPad7,[1-2]", machine_id):
                    model = "iPad Pro 2 (12.9 Inch)"
                elif fullmatch(r"iPad7,[3-4]", machine_id):
                    model = "iPad Pro (10.5 Inch)"
                elif fullmatch(r"iPad8,[1-4]", machine_id):
                    model = "iPad Pro (11 Inch)"
                elif fullmatch(r"iPad8,[5-8]", machine_id):
                    model = "iPad Pro 3 (12.9 Inch)"
                elif fullmatch(r"iPad8,[9-10]", machine_id):
                    model = "iPad Pro 4 (11 Inch)"
                elif fullmatch(r"iPad8,1[1-2]", machine_id):
                    model = "iPad Pro 4 (12.9 Inch)"
                elif fullmatch(r"iPad2,[5-7]", machine_id):
                    model = "iPad mini"
                elif fullmatch(r"iPad4,[4-6]", machine_id):
                    model = "iPad mini 2"
                elif fullmatch(r"iPad4,[7-9]", machine_id):
                    model = "iPad mini 3"
                elif fullmatch(r"iPad5,[1-2]", machine_id):
                    model = "iPad mini 4"
                elif fullmatch(r"iPad11,[1-2]", machine_id):
                    model = "iPad mini 5"
                
                # iPhones
                elif machine_id == "iPhone1,1":
                    model = "iPhone"
                elif machine_id == "iPhone1,2":
                    model = "iPhone 3G"
                elif machine_id == "iPhone2,1":
                    model = "iPhone 3GS"
                elif fullmatch(r"iPhone3,[1-3]", machine_id):
                    model = "iPhone 4"
                elif machine_id == "iPhone4,1":
                    model = "iPhone 4S"
                elif fullmatch(r"iPhone5,[1-2]", machine_id):
                    model = "iPhone 5"
                elif fullmatch(r"iPhone5,[3-4]", machine_id):
                    model = "iPhone 5c"
                elif fullmatch(r"iPhone6,[1-2]", machine_id):
                    model = "iPhone 5s"
                elif machine_id == "iPhone7,2":
                    model = "iPhone 6"
                elif machine_id == "iPhone7,1":
                    model = "iPhone 6 Plus"
                elif machine_id == "iPhone8,1":
                    model = "iPhone 6s"
                elif machine_id == "iPhone8,2":
                    model = "iPhone 6s Plus"
                elif machine_id == "iPhone8,4":
                    model = "iPhone SE (1st generation)"
                elif fullmatch(r"iPhone9,[13]", machine_id):
                    model = "iPhone 7"
                elif fullmatch(r"iPhone9,[24]", machine_id):
                    model = "iPhone 7 Plus"
                elif fullmatch(r"iPhone10,[14]", machine_id):
                    model = "iPhone 8"
                elif fullmatch(r"iPhone10,[25]", machine_id):
                    model = "iPhone 8 Plus"
                elif fullmatch(r"iPhone10,[36]", machine_id):
                    model = "iPhone X"
                elif machine_id == "iPhone11,2":
                    model = "iPhone XS"
                elif fullmatch(r"iPhone11,[46]", machine_id):
                    model = "iPhone XS Max"
                elif machine_id == "iPhone11,8":
                    model = "iPhone XR"
                elif machine_id == "iPhone12,1":
                    model = "iPhone 11"
                elif machine_id == "iPhone12,3":
                    model = "iPhone 11 Pro"
                elif machine_id == "iPhone12,5":
                    model = "iPhone 11 Pro Max"
                elif machine_id == "iPhone12,8":
                    model = "iPhone SE (2nd generation)"
                elif machine_id == "iPhone13,1":
                    model = "iPhone 12 mini"
                elif machine_id == "iPhone13,2":
                    model = "iPhone 12"
                elif machine_id == "iPhone13,3":
                    model = "iPhone 12 Pro"
                elif machine_id == "iPhone13,4":
                    model = "iPhone 12 Pro Max"
                elif machine_id == "iPhone14,4":
                    model = "iPhone 13 mini"
                elif machine_id == "iPhone14,5":
                    model = "iPhone 13"
                elif machine_id == "iPhone14,2":
                    model = "iPhone 13 Pro"
                elif machine_id == "iPhone14,3":
                    model = "iPhone 13 Pro Max"
                elif machine_id == "iPhone14,6":
                    model = "iPhone SE (3rd generation)"
                elif machine_id == "iPhone14,7":
                    model = "iPhone 14"
                elif machine_id == "iPhone14,8":
                    model = "iPhone 14 Plus"
                elif machine_id == "iPhone15,2":
                    model = "iPhone 14 Pro"
                elif machine_id == "iPhone15,3":
                    model = "iPhone 14 Pro Max"

                # iPods
                elif machine_id == "iPod1,1":
                    model = "iPod touch"
                elif machine_id == "iPod2,1":
                    model = "iPod touch 2G"
                elif machine_id == "iPod3,1":
                    model = "iPod touch 3G"
                elif machine_id == "iPod4,1":
                    model = "iPod touch 4G"
                elif machine_id == "iPod5,1":
                    model = "iPod touch 5G"
                elif machine_id == "iPod7,1":
                    model = "iPod touch 6G"
                elif machine_id == "iPod9,1":
                    model = "iPod touch 7G"
                
                # if it's not listed here
                else:
                    model = machine_id
            else:
                model = sp.getoutput('sysctl -n hw.model')
                kexts = sp.getoutput("kextstat")
                
                if "FakeSMC" in kexts or "VirtualSMC" in kexts:
                    model = f"{model} (Hackintosh)"
        
        for info in oem_info:
            model = sub(info, "", model)
        
        if "Standard PC" in model:
            model = f"{model} (KVM)"
            
        if model == "":
            model = "Unknown"
        
        return model
    
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

    def add_item(self, icon: str, name: str, content: str, color: str) -> str:
        return f"│ {self.colors[color]}{icon} {self.colors['reset']}{name.ljust(9)}│ {self.colors[color]}{content}{self.colors['reset']}\n"

    def main(self) -> None:
        out = ""
        out += "╭────────────╮\n"
        out += self.add_item("", "user", os.environ.get('USER'), "red")
        out += self.add_item("", "model", self.get_model(), "yellow")
        out += self.add_item("", "os", self.get_os_version(), "green")
        out += self.add_item("", "cpu", f"{get_cpu_info()['brand_raw']} ({machine()})", "cyan")
        out += self.add_item("", "packages", self.get_packages(), "blue")
        out += self.add_item("", "shell", os.environ.get('SHELL').split("/")[-1], "purple")
        out += self.add_item("", "memory", self.get_memory_usage(), "red")
        out += self.add_item("", "uptime", self.get_uptime(), "yellow")
        out += "├────────────┤\n"
        out += self.add_item("", "colors", f"{self.colors['black']}● {self.colors['red']}● {self.colors['yellow']}● {self.colors['green']}● {self.colors['cyan']}● {self.colors['blue']}● {self.colors['purple']}● {self.colors['reset']}●", "reset")
        out += "╰────────────╯"
        
        print(out)
            