# https://maps.heigit.org/osm-wms/service?
from owslib.wms import WebMapService
wms = WebMapService('https://maps.heigit.org/osm-wms/service?', version='1.1.1')

print(list(wms.contents))
img = wms.getmap(layers=["osm_auto:all"],
                 srs='EPSG:4326',
                 bbox=(-112, 36, -106, 41),
                 size=(300, 250),
                 format='image/jpeg',
                 transparent=True
                )
out = open('jpl_mosaic_visb.jpg', 'wb')
out.write(img.read())
out.close()