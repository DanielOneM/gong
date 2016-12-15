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
    isLeaf = True
    template_name = "functest.html"

    def render_GET(self, request):
        ctx = {
            'title': 'ONEm testing app - Functional testing',
            'user': 'Daniel Enache'
        }
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')

class StressPage(Resource):
    isLeaf = True
    template_name = "stresstest.html"

    def render_GET(self, request):
        ctx = {
            'title': 'ONEm testing app - Stress testing',
            'user': 'Daniel Enache'
        }
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')


class SettingsPage(Resource):
    isLeaf = False

    def getChild(self, name, request):
        return DynamicSettingsPage(name)


class DynamicSettingsPage(Resource):
    def __init__(self, name):
        Resource.__init__(self)
        self.template_name = name + '.html'

    def render_GET(self, request):
        ctx = {
            'title': 'ONEm testing app - Stress testing',
            'user': 'Daniel Enache',
            'connections' : [
                        {'name': 'first jasmin'},
                        {'name': 'second jasmin'}
                    ],
            'tests' :[
                        {'description': 'full test',
                         'service': 'weather'},
                        {'description': 'full test',
                         'service': 'news'}
                    ],
            'operators': [
                        {'name': 'vodafone',
                         'connection': 'first jasmin',
                         'numbers': '43'},
                        {'name': 'orange',
                         'connection': 'second jasmin',
                         'numbers': '143'}
                    ]
        }
        
        template = jinja.get_template(self.template_name)
        return template.render(ctx).encode('utf-8')
        

root = DashPage()
root.putChild('static', File(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')))
root.putChild('functional', FuncPage())
root.putChild('stress', StressPage())
root.putChild('settings', SettingsPage())

factory = Site(root)
reactor.listenTCP(5000, factory)
reactor.run()
