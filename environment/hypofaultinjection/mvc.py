from flask import Flask, request, render_template

app = Flask(__name__)


class TestObject(object):
    def __init__(self, name):
        self._name = name
    
    @property
    def name(self):
        return self._name


@app.route('/')
def main_page():
    """Returns the main page."""
    names = []
    names.append(TestObject('Jose'))
    names.append(TestObject('Emanuel'))
    names.append(TestObject('Davi'))
    return render_template('index.html', entries=names)


if __name__ == '__main__':
    app.run(port=8080)