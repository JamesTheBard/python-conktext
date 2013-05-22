from __future__ import division
import curses
import locale
import psutil
from collections import OrderedDict
from Bars import VerticalBar, HorizontalBar, HorizontalText, HorizontalBarWithData
import commands
import re
import socket
from datetime import timedelta


locale.setlocale(locale.LC_ALL, "")
coding = locale.getpreferredencoding()

class Screen(object):

    def __init__(self, screen):
        self.screen = screen
        self.get_dimensions()
        self.screen.nodelay(1)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        self.screen.scrollok(0)

    def get_dimensions(self):
        self.height, self.width = self.screen.getmaxyx()
        return (self.height, self.width)

    def main_loop(self):
        pass

class CpuBar(VerticalBar):

    def colors(self):
        colors = {
            "title": self.RED | curses.A_BOLD,
            "border": self.WHITE,
            "seperator": self.BLACK | curses.A_BOLD,
        }

        levels = {
            50: self.GREEN,
            80: self.YELLOW | curses.A_BOLD,
            100: self.RED,
        }
        self.set_colors(colors)
        self.set_fill_percentage(levels)

    def get_cpu_values(self, test=False):
        cpus = psutil.cpu_percent(interval=1, percpu=True)
        if test is True:
            cpus = [100.0, 85.0, 70.0, 55.0, 40.0, 25.0, 10.0, 0.0]
        cpu_labels = range(0, len(cpus))
        cpu_labels = [str(v) for v in cpu_labels]
        cpu_list = OrderedDict()
        for i in range(0, len(cpus)):
            label = cpu_labels[i]
            value = cpus[i]
            cpu_list[label] = value
        return cpu_list

    def update(self):
        self.update_window("CPU", self.get_cpu_values(test=False))

class MemBar(VerticalBar):

    def colors(self):
        colors = {
            "title": self.RED | curses.A_BOLD,
            "border": self.WHITE,
            "seperator": self.BLACK | curses.A_BOLD,
        }

        levels = {
            50: self.GREEN,
            80: self.YELLOW,
            95: self.RED,
        }
        self.set_colors(colors)
        self.set_fill_percentage(levels)

    def get_mem_values(self):
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()
        mem_list = OrderedDict()
        mem_list["V"] = virtual.percent
        mem_list["S"] = swap.percent
        return mem_list

    def update(self):
        self.update_window("Mem", self.get_mem_values())

class MemHoriz(HorizontalBar):

    def colors(self):
        colors = {
            "title": self.RED | curses.A_BOLD,
            "border": self.WHITE,
            "seperator": self.BLACK | curses.A_BOLD,
        }

        levels = {
            50: self.GREEN,
            80: self.BLUE,
            95: self.RED,
        }
        self.set_colors(colors)
        self.set_fill_percentage(levels)

    def get_mem_value(self):
        vmemory = psutil.virtual_memory()
        smemory = psutil.swap_memory()
        return [vmemory.percent, smemory.percent]

    def make_header(self, header_left, header_right):
        width = self.width - 4 - len(header_left) - len(header_right)
        title = header_left + (" " * width) + header_right
        return title

    def update(self):
        values = OrderedDict()
        percent = float(self.get_mem_value()[0])
        header_left = "Virtual Memory"
        header_right = "%3.1f%%" % percent
        title = self.make_header(header_left, header_right)
        values[title] = float(self.get_mem_value()[0])
        percent = float(self.get_mem_value()[1])
        header_left = "Swap Memory"
        header_right = "%3.1f%%" % percent
        title = self.make_header(header_left, header_right)
        values[title] = float(self.get_mem_value()[1])
        self.update_window("", values, offset=1)

class DiskUsage(HorizontalBarWithData):

    def colors(self):
        colors = {
            "title": self.RED | curses.A_BOLD,
            "border": self.WHITE,
            "seperator": self.BLACK | curses.A_BOLD,
        }

        levels = {
            80: self.RED,
            70: self.YELLOW | curses.A_BOLD,
            20: self.GREEN,
        }

        self.set_colors(colors)
        self.set_fill_percentage(levels)
    
    def convert_data(self, bytes, metric=False):
        bytes = long(bytes)
        abbrevs = ()
        if metric is False:
            abbrevs = ( 
                (1<<50L, 'PiB'),
                (1<<40L, 'TiB'),
                (1<<30L, 'GiB'),
                (1<<20L, 'MiB'),
                (1<<10L, 'kiB'),
                (1, 'B')
            )
        else:
            abbrevs = (
                (1000**5L, 'PB'),
                (1000**4L, 'TB'),
                (1000**3L, 'GB'),
                (1000**2L, 'MB'),
                (1000, 'kB'),
                (1, 'B')
            )
        if bytes == 1:
            return "1 byte"
        for factor, suffix in abbrevs:
            if bytes >= factor:
                break
        return '%i %s' % (bytes / factor, suffix)

    def get_data(self, directories):
        a = OrderedDict()
        for directory in directories:
            usage = psutil.disk_usage(directory)
            percent = usage.percent
            used = self.convert_data(usage.used, metric=False)
            total = self.convert_data(usage.total, metric=False)
            title = "Directory %s" % directory
            text = "%s / %s" % (used, total)
            a[title] = [text, percent]
        return a

    def update(self):
        directories = [
            "/",
            "/boot",
            "/tmp"
        ]
        self.update_window("", self.get_data(directories), offset=1)

class ComputerInfo(HorizontalText):

    def colors(self):
        colors = {
            "title": self.RED | curses.A_BOLD,
            "border": self.WHITE,
            "text": self.WHITE | curses.A_BOLD,
            "seperator": self.BLACK | curses.A_BOLD,
        }

        self.set_colors(colors)

    def get_info(self):
        a = OrderedDict()
        a["IP Address"] = self.ip_address("eth0")
        a["Hostname"] = self.hostname()
        a["Uptime"] = self.uptime()
        return a

    def ip_address(self, interface):
        ipinfo = commands.getoutput("ifconfig %s" % interface)
        ipinfo = ipinfo.split("\n")
        regex = "inet ([0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}) "
        match = re.search(regex, ipinfo[1])
        if match:
            return match.group(1)
        return "Unknown"
        
    def hostname(self):
        hostname = socket.gethostname()
        return hostname

    def uptime(self):
        with open('/proc/uptime', 'r') as f:
            seconds = float(f.readline().split()[0])
            uptime = str(timedelta(seconds=seconds)).rstrip("0")
            uptime = uptime.rstrip('.')
        return uptime

    def update(self):
        values = self.get_info()
        self.update_window("", values, offset=1)

class BatteryBar(HorizontalBarWithData):

    def colors(self):
        colors = {
            "title": self.RED | curses.A_BOLD,
            "border": self.WHITE,
        }

        levels = {
            100: self.BLUE | curses.A_BOLD,
            99: self.GREEN | curses.A_BOLD,
            70: self.YELLOW | curses.A_BOLD,
            20: self.RED,
        }

        self.set_colors(colors)
        self.set_fill_percentage(levels)

    def is_charging(self):
        data = commands.getoutput("acpi -b")
        regex = r'(Disc|Char)[^0-9]*([0-9]{1,3})%.*([0-9]{2}).([0-9]{2}).([0-9]{2})'
        regex_full = r'Full'
        match_full = re.search(regex_full, data)
        if match_full:
            title = "Battery: 100% charged"
            percent = ["On AC Power", "100"]
            return (title, percent)
        match = re.search(regex, data)
        if match:
            title = match.group(1)
            percent = match.group(2)
            time_hour = match.group(3)
            time_min = match.group(4)
            time_sec = match.group(5)
            if title == "Disc": caption = "Batt"
            if title == "Char": caption = "AC"
        if not match:
            return ("Unknown", ["", 0.0])
        if title == "Char":
            title = "Battery: %s%%" % percent
            time = "On AC - %s:%s" % (time_hour, time_min)
        else:
            title = "Battery: %s%%" % percent
            time = "Unplugged - %s:%s" % (time_hour, time_min)
        return (title, [time, percent])

    def update(self):
        title, text = self.is_charging()
        a = OrderedDict()
        a[title] = [text[0], float(text[1])]
        self.update_window(title, a, offset=1)

class Display(Screen):

    def __init__(self, screen):
        super(Display, self).__init__(screen)
        self.screen = screen
        self.window_list = []
        self.widget_setup()

    def widget_setup(self):
        self.window_list.append(CpuBar(10, 19, 1, 1, self.screen))
        self.window_list.append(MemBar(10, 7, 1, 20, self.screen))
        self.window_list.append(MemHoriz(7, 26, 11, 1, self.screen))
        self.window_list.append(BatteryBar(5, 26, 18, 1, self.screen))
        self.window_list.append(DiskUsage(13, 26, 23, 1, self.screen))
        self.window_list.append(ComputerInfo(10, 26, 36, 1, self.screen))

    def update_all(self):
        for window in self.window_list:
            window.update()

    def main_loop(self):
        while 1:
            key = self.screen.getch()
            if key == ord("q"): break
            self.update_all()

def main(stdscr):
    mon = Display(stdscr)
    mon.main_loop()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
