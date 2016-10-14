from twisted.internet import reactor
from twisted.web.resource import Resource, NoResource
from twisted.web.static import File
from twisted.web.server import Site

from config import jinja
import os


class MyResource(Resource):
    isLeaf = False
    template_name = "index.html"

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        ctx = {
            'title': 'ONEm testing app',
            'user': 'Daniel Enache'
        }
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')

root = MyResource()
root.putChild('static', File(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')))
factory = Site(root)
reactor.listenTCP(5000, factory)
reactor.run()
