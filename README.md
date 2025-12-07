# LehnNet
**Secure, lightweight and fully encrypted TCP communication layer powered by LeCatchu v9 (LehnCATH4)**

![LehnNet Logo](lehnnet.png)

LehnNet is a drop-in encrypted socket wrapper that turns any standard TCP connection into a fully encrypted, authenticated, and highly configurable secure channel using the ultra-lightweight and extremely secure **LeCatchu v9** stream cipher engine.

No external dependencies except standard Python libraries.

## Features

- End-to-end encryption with LeCatchu v9 (BLAKE2b-based keystream + multi-layer optional hardening)
- Automatic IV/nonce handling
- Perfect forward secrecy per connection (when IV enabled)
- Drop-in replacement for `socket.socket` (most methods preserved)
- Optional global encrypted proxy mode via **WorldConnectServer (WCS)**
- Works over any network: LAN, VPN, Tor, public internet
- Extremely lightweight (~170 LOC total LehnNet.py)
- Supports both client and server mode

## Installation

```bash
git clone https://github.com/aertsimon90/LehnNet.git
cd LehnNet
# Just copy LeCatchu.py and LehnNet.py into your project
```

No pip package needed — pure Python single-file design.

## Basic Usage

### Simple Encrypted Direct Connection

```python
from LehnNet import LehnNet_TCPSocket

# Server side
server = LehnNet_TCPSocket(key="MySecretPassword123")
server.bind(("0.0.0.0", 9999))
server.listen(5)

client, addr = server.accept()
print("Connected:", addr)
client.sendall(b"Hello from encrypted server!")
print(client.recv(1024))

# Client side
client = LehnNet_TCPSocket(key="MySecretPassword123")
client.connect(("server-ip", 9999))
print(client.recv(1024))  # b"Hello from encrypted server!"
client.sendall(b"Thanks!")
client.close()
```

### Internet Access via Encrypted Proxy (WorldConnectServer)

First start the WCS proxy server (can be anywhere in the world):

```python
from LehnNet import LehnNet_WorldConnectServer, LehnNet_TCPSocket

# Run this on a VPS or home server with public IP
wcs = LehnNet_WorldConnectServer(LehnNet_TCPSocket(key="SpecialKey123"), addr=("0.0.0.0", 38483))
wcs.start()  # Keeps running and proxies all traffic encrypted
```

Then use it from anywhere (even behind NAT/CGNAT):

```python
from LehnNet import LehnNet_TCPSocket

# Connect to any site on the internet through your encrypted proxy
s = LehnNet_TCPSocket(key="SpecialKey123", wcs=("your-vps-ip", 38483))

s.connect(("google.com", 80))
s.sendall(b"GET / HTTP/1.1\r\nHost: www.google.com\r\nConnection: close\r\n\r\n")

response = b""
while True:
    data = s.recv(4096)
    if not data:
        break
    response += data
print(response.decode(errors="ignore"))

s.close()
```

You now have fully encrypted outbound internet access through your own proxy — ideal for privacy, bypassing restrictions, or secure remote access.

## Advanced Options

```python
socket = LehnNet_TCPSocket(
    key="StrongKey!@#2025",
    xbase=4,           # Higher = stronger but slower keystream
    iv=True,           # Recommended (default)
    ivlength=512,      # Larger IV = more security
    ivxbase=4
)
```

## Security Notes

- Uses LeCatchu v9 — one of the lightest yet cryptographically strong stream ciphers
- Key is strengthened using multi-round BLAKE2b-based KDF (Optionally, you can use LeCustomHash)
- All communication is encrypted and authenticated (when using `.accept()`/`.connect()`)

## License

MIT License — free for personal and commercial use.

---

**LehnNet — Because your traffic should only be readable by you.**

Made with passion by the LeCatchu Project
