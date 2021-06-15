from stem import process
from stem import Signal
from stem.control import Controller
import sys
import requests

SOCKS_PORT = 9051
CONTROL_PORT = 9071


def bootstrap(line):
    if "Bootstrapped" in line:
        sys.stdout.write("\r" + line)
        sys.stdout.flush()


print("Reading exit-addresses\n")
req = requests.get("https://check.torproject.org/exit-addresses",
                   proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"})
nodes = [x.split(" ")[1] for x in req.text.split("\n") if "ExitNode" in x]
tor_process = []


def tor(x, con):
    print(f"\n\n[+] launching tor on {x}:\n")
    try:
        tor_process.append(process.launch_tor_with_config(
            config={
                'SocksPort': str(x),
                'ExitNodes': nodes[x - SOCKS_PORT],
                'ControlPort': str(con),
                'DataDirectory': 'data/tor' + str(x),
            },
            init_msg_handler=bootstrap,
        ))
    except Exception as er:
        print()
        print(er)


def change_ip(con_port):
    print("[+] Changing IP Address...")
    with Controller.from_port(port=con_port) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


tor_nm = int(input("run clients: "))
for i in range(tor_nm):
    port = SOCKS_PORT + i
    control_port = CONTROL_PORT + i
    tor(port, control_port)
del nodes, req
print("\n\nAll Tor clients running successful\n\nPress Enter to continue.....")
input()
count = 0
while 1:
    uri = input("\n\nurl: ")
    if uri == "exit":
        break
    port = SOCKS_PORT + count
    try:
        r = requests.get(uri, proxies={"http": f"socks5://127.0.0.1:{port}", "https": f"socks5://127.0.0.1:{port}"})
    except requests.exceptions.ConnectionError:
        print(f"connection error with port {port}")
        change_ip(CONTROL_PORT + count)
        continue
    print(
        f"Request Info:\n\turl: {uri}\n\ttor port: {port}\n\tstatus code: {r.status_code}\n\tcookies: "
        f"{dict(r.cookies)}"
    )
    count += 1
    if count == tor_nm:
        count = 0

for x in range(len(tor_process)):
    print(f"stopping {SOCKS_PORT + x}")
    tor_process[x].kill()
