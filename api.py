import sys
import json
import re
import inspect
import importlib
import sqlite3
from flask import Flask, request, abort
import yaml
from attrdict import AttrDict

config_file = 'sample_config.yml'
if len(sys.argv) > 1:
    if sys.argv[1]:
        config_file = sys.argv[1]

with open(config_file) as f:
    config = AttrDict(yaml.load(f))

DB = 'db.sqlite'
app = Flask(__name__)
init_sql = config.init.db
init_module = config.init.module

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

# Detect whether `string` refers to a function in custom modules
def is_python_function(string):
    for module in init_module:
        if re.match(r'^%s\.[a-zA-Z_][a-zA-Z0-9_]*$' % module, string.strip()):
            return True
    return False

# Extract parameter values in requests
def get_param_value(param_name):
    result = {}
    if type(param_name) is str:
        param_name = [param_name]
    for key in param_name:
        value = request.args.get(key)
        if request.json:
            value = request.json.get(param_name) if not value else value
        if value:
            result[key] = value
    return result


# Handle requests according to methods defined in config.api[route]
def handler(**kwargs):
    route = request.url_rule.rule
    method = request.method
    for sql in config.api[route][method]:
        if is_python_function(sql):
            module = importlib.import_module(sql.split('.')[0])
            try:
                function = module.__dict__[sql.split('.')[1]]
                params = inspect.getargspec(function)[0]
                param_values = get_param_value(params)
                for key in param_values:
                    if key not in kwargs:
                        kwargs[key] = param_values[key]
                return json.dumps(function(**kwargs), indent=2)
            except TypeError as e:
                # Not enough parameters
                print(e)
                continue
            except KeyError as e:
                # Undefined function or possibly a sql 
                print(e)
                pass
        # print(route, method, sql)
        params = re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', sql)
        # remove `{` and `}`
        params = [param[1:-1] for param in params]
        param_values = get_param_value(params)
        for key in param_values:
            if key not in kwargs:
                kwargs[key] = param_values[key]
        if can_parameterize(sql, kwargs):
            keys = [key[1:-1] for key in re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', sql)]
            values = [kwargs[key] for key in keys]
            sql = re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', '?', sql)
            result = execute(sql, values)
            return json.dumps(result, indent=2)
    return json.dumps({'msg': 'Insufficient parameters.'}, indent=2)
        
# Parse multiple routes in one rule
api = {}
for url in config.api:
    routes = re.split(r',\s+', url)
    for route in routes:
        route = route.strip()
        if route not in api:
            api[route] = {}
        for method in config.api[url]:
            if method not in api[route]:
                api[route][method] = []
            api[route][method] += config.api[url][method]
config.update({'api': api})

# Add url rule for each route
for route in config.api:
    # only choose one sql to execute which matches the parameter
    handler.methods = [method for method in config.api[route]]
    app.add_url_rule(route, '{}-{}'.format(route, handler), handler)


if __name__ == "__main__":
    execute(init_sql)
    for module in init_module:
        importlib.import_module(module)
    app.run(host='0.0.0.0', debug=True)
    pass

