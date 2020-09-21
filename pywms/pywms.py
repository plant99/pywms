from owslib.wms import WebMapService

from flask import Flask, request, make_response
import urllib
import logging
from io import BytesIO, StringIO

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.offsetbox import AnchoredText

from shapely.geometry import shape 
import json
from PIL import Image
from cartopy.io.img_tiles import Stamen

app = Flask(__name__)
wms = WebMapService('https://maps.heigit.org/osm-wms/service?', version='1.1.1')

class WMSServer(object):

    def __init__(self):
        self.tiler = Stamen('terrain-background')
        self.mercator = self.tiler.crs
        pass

    def get_capabilities(self, server_url=None):
        return "capap", "text/plain"

    def produce_plot(self, query, mode):
        # parse bbox
        bbox = tuple(query.get("bbox").split(","))
        bbox = [float(i) for i in bbox]

        bounds = [bbox[0], bbox[2], bbox[1],  bbox[3]]

        fig = Figure()
        ax = fig.add_subplot(1, 1, 1, projection=self.mercator)
        ax.set_extent(bounds, crs=ccrs.PlateCarree())

        # Put a background image on for nice sea rendering.
        # ax.stock_img()

        # add custom shape
        shp = shape({
            "type": "Polygon",
            "coordinates": [
              [
                [
                  67.236328125,
                  22.268764039073968
                ],
                [
                  62.13867187499999,
                  11.609193407938953
                ],
                [
                  77.95898437499999,
                  10.487811882056695
                ],
                [
                  79.453125,
                  19.145168196205297
                ],
                [
                  74.1796875,
                  22.59372606392931
                ],
                [
                  67.236328125,
                  22.268764039073968
                ]
              ]
            ]
          })
        shapely_feature = cfeature.ShapelyFeature([shp], crs=ccrs.PlateCarree())
        ax.add_feature(shapely_feature)
        ax.add_image(self.tiler, 6)
        figdata = BytesIO()

        fig.savefig(figdata, bbox_inches='tight', format='jpeg', pad_inches=0)
        figdata.seek(0)
        return figdata.read(), "image/png"

server = WMSServer()


@app.route('/')
def application():
    if request.query_string == b'':
        res = make_response("invalid request", 200)
        return res
    try:
        # Request info
        query = request.args

        # Processing
        # ToDo Refactor
        request_type = query.get('request')
        if request_type is None:  # request_type may *actually* be set to None
            request_type = ''
        request_type = request_type.lower()
        request_service = query.get('service', '')
        request_service = request_service.lower()
        request_version = query.get('version', '')

        url = request.url
        server_url = urllib.parse.urljoin(url, urllib.parse.urlparse(url).path)
        if (request_type in ('getcapabilities', 'capabilities') and
                request_service == 'wms' and request_version in ('1.1.1', '')):
            return_data, return_format = server.get_capabilities(server_url)
        elif request_type in ('getmap', 'getvsec') and request_version in ('1.1.1', ''):
            return_data, return_format = server.produce_plot(query, request_type)
        else:
            logging.debug("Request type '%s' is not valid.", request)
            raise RuntimeError("Request type is not valid.")

        res = make_response(return_data, 200)
        response_headers = [('Content-type', return_format), ('Content-Length', str(len(return_data)))]
        for response_header in response_headers:
            res.headers[response_header[0]] = response_header[1]
        return res

    except Exception as ex:
        error_message = "{}: {}\n".format(type(ex), ex)
        error_message = error_message.encode("utf-8")

        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(error_message)))]
        res = make_response(error_message, 404)
        for response_header in response_headers:
            res.headers[response_header[0]] = response_header[1]
        return res

if __name__ == "__main__":
    app.run()
