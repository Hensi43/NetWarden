import logging
import threading
from scapy.all import sniff, TCP, TLS
from scapy.layers.tls.extensions import TLS_Ext_ServerName
from scapy.layers.tls.handshake import TLSClientHello
from collections import deque
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SNI-Sniffer")

class SNISniffer:
    def __init__(self, interface="en0"):
        self.interface = interface
        self.domains_detected = deque(maxlen=50) # Keep last 50 domains
        self.running = False

    def start(self):
        self.running = True
        logger.info(f"Starting SNI Sniffer on {self.interface}...")
        
        # Current scapy TLS support might need explicit loading or older methods.
        # We will use a raw packet callback for robustness.
        self.thread = threading.Thread(target=self._sniff_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False


    def _sniff_loop(self):
        # Filter for TCP port 443 (HTTPS)
        try:
            sniff(
                iface=self.interface, 
                filter="tcp port 443", 
                prn=self._process_packet, 
                store=0,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            logger.error(f"Sniffer crashed: {e}")

    def _process_packet(self, packet):
        try:
            if packet.haslayer(TLSClientHello):
                # Scapy's TLS parser is powerful
                client_hello = packet[TLSClientHello]
                for ext in client_hello.extensions:
                    if isinstance(ext, TLS_Ext_ServerName):
                        for server_name in ext.servernames:
                            domain = server_name.servername.decode('utf-8')
                            self._log_detection(domain)
                            return
            
            # Fallback: Manual byte inspection if scapy TLS layer fails or isn't perfect
            # (Sometimes needed for partial packets)
            if packet.haslayer(TCP) and packet[TCP].payload:
                payload = bytes(packet[TCP].payload)
                if self._is_tls_client_hello(payload):
                    domain = self._extract_sni(payload)
                    if domain:
                        self._log_detection(domain)

        except Exception as e:
            pass

    def _log_detection(self, domain):
        logger.info(f"Detected: {domain}")
        self.domains_detected.append({'time': time.time(), 'domain': domain})

    # --- Low Level Parsers (Robustness against complex scapy layer issues) ---
    def _is_tls_client_hello(self, payload):
        # TLS Record Type 0x16 (Handshake), Version >= 0x0301 (TLS 1.0)
        # Handshake Type 0x01 (Client Hello)
        if len(payload) > 5 and payload[0] == 0x16 and payload[5] == 0x01:
            return True
        return False

    def _extract_sni(self, payload):
        try:
            # Skip Record Header (5) + Handshake Header (4) + Random (32) + SessionID Len (1)
            offset = 5 + 4 + 32 + 1 
            session_id_len = payload[offset-1]
            offset += session_id_len
            
            # Cipher Suites Len (2)
            if offset + 2 > len(payload): return None
            cipher_suites_len = int.from_bytes(payload[offset:offset+2], 'big')
            offset += 2 + cipher_suites_len
            
            # Compression Methods Len (1)
            if offset + 1 > len(payload): return None
            comp_len = payload[offset]
            offset += 1 + comp_len
            
            # Extensions Len (2)
            if offset + 2 > len(payload): return None
            extensions_len = int.from_bytes(payload[offset:offset+2], 'big')
            offset += 2
            
            end_ext = offset + extensions_len
            while offset < end_ext:
                if offset + 4 > len(payload): break
                ext_type = int.from_bytes(payload[offset:offset+2], 'big')
                ext_len = int.from_bytes(payload[offset+2:offset+4], 'big')
                offset += 4
                
                if ext_type == 0: # SNI Extension
                    # SNI List Len (2)
                    sni_list_len = int.from_bytes(payload[offset:offset+2], 'big')
                    offset += 2
                    # SNI Type (1) + SNI Len (2)
                    sni_len = int.from_bytes(payload[offset+1:offset+3], 'big')
                    domain_bytes = payload[offset+3:offset+3+sni_len]
                    return domain_bytes.decode('utf-8')
                
                offset += ext_len
        except Exception:
            pass
        return None

if __name__ == "__main__":
    # Test Run
    sniffer = SNISniffer("en0") # Adjust interface if needed
    try:
        sniffer.start()
        print("Listening for encrypted traffic... Open a browser and visit sites.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sniffer.stop()
