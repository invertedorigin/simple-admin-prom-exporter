import time
import logging
import requests
from prometheus_client import Gauge, start_http_server
from prometheus_client.exposition import generate_latest
from prometheus_client import CollectorRegistry

class CustomMetric:
    def __init__(self, url, status, total_ms, dns_ms, firstbyte_ms, connect_ms,
                 state, mode, duplex_mode, mcc, mnc, cell_id, pcid, tac, arfcn,
                 band, nwDLBW, rsrp, rsrq, sinr, txpower):
        self.url = url
        self.status = status
        self.total_ms = total_ms
        self.dns_ms = dns_ms
        self.firstbyte_ms = firstbyte_ms
        self.connect_ms = connect_ms
        self.state = state
        self.mode = mode
        self.duplex_mode = duplex_mode
        self.mcc = mcc
        self.mnc = mnc
        self.cell_id = cell_id
        self.pcid = pcid
        self.arfcn = arfcn
        self.band = band
        self.nwDLBW = nwDLBW
        self.rsrp = rsrp
        self.rsrq = rsrq
        self.sinr = sinr
        self.txpower = txpower

class Exporter:
    def __init__(self, interval, urls):
        if not urls:
            logging.warning("No URLs provided to exporter")

        self.registry = CollectorRegistry()

        self.url_status = Gauge('url_status', 'Status of the URL as a integer value', ['url'], registry=self.registry)
        self.url_ms = Gauge('url_response_ms', 'Response time in milliseconds it took for the URL to respond.', ['url'], registry=self.registry)
        self.url_dns = Gauge('url_dns_ms', 'Response time in milliseconds it took for the DNS request to take place.', ['url'], registry=self.registry)
        self.url_first_byte = Gauge('url_first_byte_ms', 'Response time in milliseconds it took to retrieve the first byte.', ['url'], registry=self.registry)
        self.url_connect_time = Gauge('url_connect_time_ms', 'Response time in milliseconds it took to establish the initial connection.', ['url'], registry=self.registry)

        self.sr_mcc = Gauge('mcc', 'Mobile country code', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_mnc = Gauge('mnc', 'Mobile network code', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_pcid = Gauge('pcid', 'Physical cell identifier', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_tac = Gauge('tac', 'Tracking area code', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_arfcn = Gauge('arfcn', 'Absolute radio-frequency channel number', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_band = Gauge('band', 'Frequency band', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_nrdlbw = Gauge('nrdlbw', 'NR DL bandwidth', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_rsrp = Gauge('rsrp', 'Reference signal received power', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_rsrq = Gauge('rsrq', 'Reference signal received quality', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_sinr = Gauge('sinr', 'Signal-to-interference-plus-noise ratio', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)
        self.sr_txpower = Gauge('txpower', 'Transmit power', ['url', 'state', 'mode', 'duplexmode', 'cellid'], registry=self.registry)

        self.interval = interval
        self.urls = urls

    def update_custom_metrics(self, cm):
        logging.info(f"Updating custom metrics: url: {cm.url}, connectMS: {cm.connect_ms}, dnsMS: {cm.dns_ms}, firstbyteMS: {cm.firstbyte_ms}, totalMS: {cm.total_ms}, status: {cm.status}")

        self.url_dns.labels(url=cm.url).set(cm.dns_ms)
        self.url_connect_time.labels(url=cm.url).set(cm.connect_ms)
        self.url_ms.labels(url=cm.url).set(cm.total_ms)
        self.url_first_byte.labels(url=cm.url).set(cm.firstbyte_ms)
        self.url_status.labels(url=cm.url).set(cm.status)

        self.sr_mcc.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.mcc)
        self.sr_mnc.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.mnc)
        self.sr_pcid.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.pcid)
        self.sr_arfcn.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.arfcn)
        self.sr_band.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.band)
        self.sr_nrdlbw.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.nwDLBW)
        self.sr_rsrp.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.rsrp)
        self.sr_rsrq.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.rsrq)
        self.sr_sinr.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.sinr)
        self.sr_txpower.labels(url=cm.url, state=cm.state, mode=cm.mode, duplexmode=cm.duplex_mode, cellid=cm.cell_id).set(cm.txpower)

    def fetch_cell_metrics(self, url):

        headers = {
            'Accept': '*/*',
            'Pragma': 'no-cache',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'http://192.168.225.1:8080/bandlock.html',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
            'Connection': 'keep-alive',
        }

        params = {
            'atcmd': 'AT+QENG="servingcell"',
        }

        response = requests.get('http://192.168.225.1:8080/cgi-bin/get_atcommand', params=params, headers=headers)

        print(response.text)

        data = response.text
        if "+QENG:" not in data:
            logging.error("Error parsing AT response")

        parts = data.split(",")
        if len(parts) < 17:
            logging.error("Error splitting data")

        try:
            state = str(parts[1])
            mode = str(parts[2])
            duplexmode = str(parts[3])
            mcc = float(parts[4])
            mnc = float(parts[5])
            cellid = str(parts[6])
            pcid = float(parts[7])
            arfcn = float(parts[9])
            band = float(parts[10])
            nrdlbw = float(parts[11])
            rsrp = float(parts[12])
            rsrq = float(parts[13])
            sinr = float(parts[14])
            txpower = float(parts[15])
        except ValueError as e:
            logging.error(f"Error converting data to float: {e}")
            return

        cm = CustomMetric(
            url=url, status=0, total_ms=0, dns_ms=0, firstbyte_ms=0, connect_ms=0,
            state=state, mode=mode, duplex_mode=duplexmode, mcc=mcc, mnc=mnc, cell_id=cellid, pcid=pcid,
            tac="", arfcn=arfcn, band=band, nwDLBW=nrdlbw, rsrp=rsrp, rsrq=rsrq,
            sinr=sinr, txpower=txpower
        )

        self.update_custom_metrics(cm)

    def run(self):
        while True:
            for url in self.urls:
                self.fetch_cell_metrics(url)
            time.sleep(self.interval)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    interval = 60  # Update interval in seconds
    urls = ["http://localhost:8000/metrics"]  # Example URLs

    exporter = Exporter(interval, urls)
    
    start_http_server(8000, registry=exporter.registry)
    
    exporter.run()
