from twisted.internet import reactor
from twisted.web.resource import Resource, NoResource
from twisted.web.static import File
from twisted.web.server import Site

from config import jinja
import os
import random


class DashPage(Resource):
    isLeaf = False
    template_name = "index.html"

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        servers = [{
            'name': 'Freewilly',
            'intesting': True,
            'color': random.choice(['green', 'red', 'yellow']),
            'ip': '123.123.123.123'
        } for _ in range(7)]
        ctx = {
            'title': 'ONEm testing app - Dashboard',
            'user': 'Daniel Enache',
            'servcol': servers

        }
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')

class FuncPage(Resource):
    isLeaf = False
    template_name = "functest.html"

    def render_GET(self, request):
        ctx = {
            'title': 'ONEm testing app - Functional testing',
            'user': 'Daniel Enache'
        }
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')

class StressPage(Resource):
    isLeaf = False
    template_name = "stresstest.html"

    def render_GET(self, request):
        ctx = {
            'title': 'ONEm testing app - Stress testing',
            'user': 'Daniel Enache'
        }
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')

root = DashPage()
root.putChild('static', File(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')))
root.putChild('functional', FuncPage())
root.putChild('stress', StressPage())

factory = Site(root)
reactor.listenTCP(5000, factory)
reactor.run()
