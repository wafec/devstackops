#!/usr/bin/env python

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from json import dumps


app = Flask(__name__)
api = Api(app)


class FaultInjectionTest(Resource):
    def post(self):
        print(request.json['message'])
        return { 'message': request.json['message'] }

    def get(self):
        return { 'test': 'working' }


api.add_resource(FaultInjectionTest, '/faultInjectionTest')


if __name__ == '__main__':
    app.run(port=5002)