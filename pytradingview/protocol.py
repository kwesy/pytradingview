import re, json, zlib, base64


cleanerRgx = '~h~'
splitterRgx = '~m~[0-9]{1,}~m~'

def parseWSPacket(string):
    l = re.split(splitterRgx, re.sub(cleanerRgx, '', string))
    # print(l)
    packet = []
    for p in l:
        if not p: continue 
        try:
            packet.append(json.loads(p))
        except:
            print("\033[;33m Can't pass\033[;0m", p, '<-')
    # print('p->', packet)
    return packet


def formatWSPacket(packet):
	if isinstance(packet, dict):
		packet = json.dumps(packet,separators=(',', ':')).replace('null', '""')
	return f'~m~{len(packet)}~m~{packet}'
    


def parseCompressed(data):
    return json.load(zlib.decompress(base64.b64decode(data)))


# print(parseWSPacket('~m~361~m~{"session_id":"<0.20865.1202>_sfo-charts-33-webchart-7@sfo-compute-33_x","timestamp":1666351503,"timestampMs":1666351503272,"release":"registry.xtools.tv/tvbs_release/webchart:release_205-101","studies_metadata_hash":"2701eef702a051bdc70e0c5e8fcce43964ebe1da","protocol":"json","javastudies":"javastudies-3.61_2654","auth_scheme_vsn":2,"via":"23.82.31.219:443"}'))