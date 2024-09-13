import pyfiglet
import psutil
import curses
import subprocess
import urllib3
import socket
import requests

art = pyfiglet.figlet_format("netview", font="rectangles")

def get_git_version():
    try:
        version = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.PIPE
        ).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        version = "Unknown"
    except FileNotFoundError:
        version = "Git Not Found"
    return version

def check_internet_conn():
    http = urllib3.PoolManager(timeout=3.0)
    try:
        r = http.request('GET', 'http://google.com', preload_content=False)
        code = r.status
        r.release_conn()
        return code == 200
    except urllib3.exceptions.RequestError:
        return False
    
def get_geo_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        city = data.get('city', 'Unknown City')
        country = data.get('country', 'Unknown Country')
        return f"{city}, {country}"
    except requests.RequestException:
        return "Unable to retrieve location"

def check_dns_resolution():
    try:
        socket.gethostbyname('google.com')
        return True
    except socket.error:
        return False

def get_lines_for_interface(data, addrs, stats, is_up):
    lines = []
    lines.append(f'Status: {"Up" if is_up else "Down"}')
    lines.append(f'Bytes Sent: {data.bytes_sent}')
    lines.append(f'Bytes Received: {data.bytes_recv}')
    lines.append(f'Packets Sent: {data.packets_sent}')
    lines.append(f'Packets Received: {data.packets_recv}')
    if addrs:
        for addr in addrs:
            lines.append(f'Address: {addr.address}')
            if addr.netmask:
                lines.append(f'Netmask: {addr.netmask}')
            if addr.broadcast:
                lines.append(f'Broadcast: {addr.broadcast}')
    if stats:
        lines.append(f'Duplex: {stats.duplex.name}')
        lines.append(f'Speed: {stats.speed} Mbps')
        lines.append(f'MTU: {stats.mtu}')
    return lines

def main(stdscr):
    curses.curs_set(0)
    hasColors = curses.has_colors()

    if hasColors:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    
    while True:
        art_row = 0
        netviewStatsY = 10
        row = len(art.splitlines())//2

        stdscr.clear()
        stdscr.attron(curses.color_pair(1))

        for line in art.splitlines():
            stdscr.addstr(art_row, netviewStatsY, line)
            art_row += 1
        
        stdscr.addstr(row + 2, netviewStatsY, f"Version: {get_git_version()}")

        connection_status = check_internet_conn()
        dns_res = check_dns_resolution()
        geo_loc = get_geo_location()

        if connection_status:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(row + 3, netviewStatsY, "Internet Connection: Connected")
        else:
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(row + 3, netviewStatsY, "Internet Connection: Disconnected")

        if dns_res:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(row + 4, netviewStatsY, "DNS Resolution: Working...")
        else:
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(row + 4, netviewStatsY, "DNS Resolution: Dead...")
        
        stdscr.attron(curses.color_pair(1))

        stdscr.addstr(row + 6, netviewStatsY, f'Location: {geo_loc}')

        stdscr.refresh()

        net_io_counters = psutil.net_io_counters(pernic=True)
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        max_y, max_x = stdscr.getmaxyx()

        for interface, data in net_io_counters.items():
            isUp = net_if_stats[interface].isup
            if isUp:
                stdscr.attron(curses.color_pair(2))
            else:
                stdscr.attron(curses.color_pair(3))

            if row < max_y:
                stdscr.addstr(row, 50, interface)
            row += 1

            stdscr.attron(curses.color_pair(1))

            lines = get_lines_for_interface(data, net_if_addrs.get(interface, []), net_if_stats.get(interface), isUp)
            for line in lines:
                if row < max_y:
                    stdscr.addstr(row, 52, line)
                row += 1
        stdscr.refresh()
        curses.napms(1000)

if __name__ == "__main__":
    curses.wrapper(main)