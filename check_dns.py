import socket
import dns.resolver

def check_dns():
    try:
        print("Checking DNS for google.com...")
        print(socket.gethostbyname('google.com'))
    except Exception as e:
        print(f"Socket gethostbyname failed: {e}")

    try:
        print("\nChecking SRV record for _mongodb._tcp.tunora.w630k5n.mongodb.net...")
        resolver = dns.resolver.Resolver()
        answers = resolver.resolve('_mongodb._tcp.tunora.w630k5n.mongodb.net', 'SRV')
        for rdata in answers:
            print(f"Target: {rdata.target}, Port: {rdata.port}")
    except Exception as e:
        print(f"DNS Resolver failed: {e}")

if __name__ == "__main__":
    check_dns()
