import urllib.request, ssl, re

ctx = ssl._create_unverified_context()
headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://www.cmfchile.cl/institucional/mercados/entidad.php?mercado=V&rut=96529070&grupo=&tipoentidad=ADGEN&row=&vigente=S&control=svs'
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req, context=ctx, timeout=30).read().decode('latin1')

print("Tabs found:")
for m in re.findall(r'<a[^>]*href=[\'"]([^\'"]*pestania=[^\'"]*)[\'"][^>]*>(.*?)</a>', html, re.I):
    print(" ", m)
