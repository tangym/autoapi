import sys
import json
import re
import inspect
import importlib
import sqlite3
from flask import Flask, request, abort
import yaml
from attrdict import AttrDict
from configure import Config


DB = 'db.sqlite'
app = Flask(__name__)

config_file = 'sample_config.yml'
if len(sys.argv) > 1:
    if sys.argv[1]:
        config_file = sys.argv[1]
config = AttrDict(Config(config_file))

# Extract parameter values in requests
def get_param_value(param_name):
    result = {}
    if type(param_name) is str:
        param_name = [param_name]
    for key in param_name:
        value = request.args.get(key)
        if request.json:
            value = request.json.get(key) if not value else value
        if value:
            result[key] = value
    return result

def execute(sql, params=[]):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if type(sql) is str:
        c.execute(sql, params)
        if c.description:
            names = [i[0] for i in c.description]
            result = [dict(zip(names, record)) for record in c.fetchall()]
        else:
            result = c.fetchall()
    else:
        result = []
        if not params:
            params = [[] for s in sql]
        for (s, param) in zip(sql, params):
            c.execute(s, param)
            if c.description:
                names = [i[0] for i in c.description]
                result += [[dict(zip(names, record)) for record in c.fetchall]]
            else:
                result += [c.fetchall()]
    conn.commit()
    conn.close()
    return result

# Detect whether `sql` can be fully parameterized by `param`
def can_parameterize(sql, param):
    try:
        sql.format(**param)
        return True
    except KeyError:
        return False

# Handle requests according to methods defined in config.api[route]
def handler(**kwargs):
    route = request.url_rule.rule
    method = request.method
    for action in config.api[route][method]:
        if callable(action):
            try:
                params = inspect.getargspec(action)[0]
                param_values = get_param_value(params)
                param_values.update(kwargs)
                return json.dumps(action(**param_values), indent=2)
            except TypeError as e:
                # Not enough parameters
                print(e)
                continue
        elif type(action) is str:
            params = re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', action)
            # remove `{` and `}`
            params = [param[1:-1] for param in params]
            param_values = get_param_value(params)
            param_values.update(kwargs)
            if can_parameterize(action, param_values):
                keys = [key[1:-1] for key in re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', action)]
                values = [param_values[key] for key in keys]
                sql = re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', '?', action)
                result = execute(sql, values)
                return json.dumps(result, indent=2)
    return json.dumps(list(
                filter(lambda url: url.startswith(route), set(config.api))))


# Add url rule for each route
for route in config.api:
    # only choose one sql to execute which matches the parameter
    handler.methods = [method for method in config.api[route]]
    app.add_url_rule(route, '{}-{}'.format(route, handler), handler)


if __name__ == "__main__":
    execute(config.init.db)
    app.run(host='0.0.0.0', debug=True)
    pass
