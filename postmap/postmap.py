from owslib.wms import WebMapService

from flask import Flask, request, make_response
import urllib
import logging

app = Flask(__name__)
wms = WebMapService('https://maps.heigit.org/osm-wms/service?', version='1.1.1')

class WMSServer(object):

    def __init__(self):
        pass

    def get_capabilities(self, server_url=None):
        return "capap", "text/plain"

    def produce_plot(self, query, mode):

        # parse bbox
        bbox = tuple(query.get("bbox").split(","))
        bbox = [float(i) for i in bbox]

        print(bbox, query.get("height"), query.get("width"))
        img = wms.getmap(layers=["osm_auto:all"],
                 srs='EPSG:4326',
                 bbox=bbox,
                 size=(query.get("height"), query.get("width")),
                 format='image/jpeg',
                 transparent=True
                )
        out = open('jpl_mosaic_visb.jpg', 'wb')
        out.write(img.read())
        out.close()
        # print(type(img))
        return img.read(), "image/jpeg"

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
