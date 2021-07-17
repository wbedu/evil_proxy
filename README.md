# evil_proxy

A Man in the Middle attack via http proxy.
Active mode injects js to steal cookies and browser data
passive mode records sensitive data

## How to Run:

```bash
./proxy.py -m passive -h 0.0.0.0 -p 80
```

## Arguments
```bash
usage: proxy.py [--help] -m MODE -h LISTENING_IP -p LISTENING_PORT [-v]

optional arguments:
  --help                show this help message and exit
  -m MODE, --mode MODE  The mode you want your proxy to operate, which will either be active or passive
  -h LISTENING_IP, --listening_ip LISTENING_IP
                        The IP address your proxy will listen on connections on
  -p LISTENING_PORT, --listening_port LISTENING_PORT
                        The port your proxy will listen for connections on
  -v, --verbosity       verbosity level
```

## Dependencies

 1. python3
 2. install python requires
 
    `pip3 install -r requirements.txt --user`