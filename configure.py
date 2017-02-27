import json
import re
import os
import sys
import inspect
import importlib
import yaml
from attrdict import AttrDict


class Config(dict):
    def __init__(self, config_file='sample_config.yml', *args):

        config_file = os.path.abspath(config_file)
        current_dir = os.getcwd()

        os.chdir(os.path.split(config_file)[0])
        default = {'init': {'db': [], 'module': [], 'yaml': []}, 'api': {}}
        try:
            with open(config_file) as f:
                self.update(yaml.load(f))
        except FileNotFoundError as fnfe:
            print('Configuration file not found: %s' % config_file)
            print('Use default configuration instead.')
        self.update(Config.fill_default_configs(self, default))

        sys.path.append(os.getcwd())
        self['init']['module'] = [importlib.import_module(module) 
                                  for module in self['init']['module']]
        configs = [Config(yml) for yml in self['init']['yaml']]
        for config in configs:
            self.join(config)

        # Find and join yaml files in api section
        route_with_yamls = {route for route in self['api']
                            if type(self['api'][route]) is str}
        for route in route_with_yamls:
            # self['api'][route] is a yaml file
            config = Config(self['api'][route])
            del self['api'][route]
            for sroute in config['api']:
                self['api'][route+sroute] = config['api'][sroute]
        os.chdir(current_dir)

        for route in self['api']:
            for method in self['api'][route]:
                self['api'][route][method] = [self.get_python_function(action) 
                                              for action in self['api'][route][method]]
        
        # Split multiple rules
        api = {}
        for url in self['api']:
            routes = re.split(r',\s+', url)
            for route in routes:
                route = route.strip()
                if route not in api:
                    api[route] = {}
                for method in self['api'][url]:
                    if method not in api[route]:
                        api[route][method] = []
                    api[route][method] += self['api'][url][method]
        self.update({'api': api})
        self = AttrDict(self)

                                             
    # Detect whether `string` refers to a function in custom modules
    def get_python_function(self, string):
        if type(string) is not str:
            return string
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$', 
                        string.strip()):
            return string
        for module in self['init']['module']:
            if module.__name__ == string.split('.')[0]:
                try:
                    return module.__dict__[string.split('.')[1]]
                except KeyError:
                    return string
                    
    # Join two Config objects
    def join(self, config):
        if isinstance(config, Config):
            self['init']['db'] += config['init']['db']
            self['init']['module'] += config['init']['module']
            self['init']['yaml'] += config['init']['yaml']
        else:
            raise TypeError(str(config) + 'is not a Config object')
    
    # Fill default configurations if not provided
    @classmethod
    def fill_default_configs(cls, config, default):
        for key in default:
            if key not in config:
                config[key] = default[key]
            elif isinstance(config[key], dict):
                config[key].update(cls.fill_default_configs(config[key], default[key]))
        return config
