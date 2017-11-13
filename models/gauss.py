import json
import collections
import numpy as np
from scipy.stats import multivariate_normal
# import matplotlib.pyplot as plt


def parse_json_parameters(func):
    def inner(*args, **kwargs):
        print(args, kwargs)
        args = [json.loads(value) if type(value) is str else value 
                                  for value in args]
        kwargs = {key: json.loads(kwargs[key]) 
                       if type(kwargs[key]) is str else kwargs[key] 
                       for key in kwargs}
        return func(*args, **kwargs)
    return inner

def parse_json(x):
    try:
        return json.loads(x)
    except:
        return x

# @parse_json_parameters
def generate_gauss_sample(mu='0', sigma='1', n='1'):
    mu, sigma, n = parse_json(mu), parse_json(sigma), parse_json(n)
    try:
        return np.random.multivariate_normal(mu, sigma, n).tolist()
    except ValueError as ve:
        return np.random.normal(mu, sigma, n).tolist()

# @parse_json_parameters
def gauss_pdf(mu='0', sigma='1', x='0'):
    mu, sigma, x = parse_json(mu), parse_json(sigma), parse_json(x)
    return multivariate_normal(mu, sigma).pdf(x).tolist()

# def plot_dataset(class1, class2):
#     for sample in class1:
#         plt.plot(sample[0], sample[1], 'r.')
#     for sample in class2:
#         plt.plot(sample[0], sample[1], 'g.')
#     plt.savefig('{}-{}.pdf'.format(len(class1), len(class2)))


# def decide(class1, class2):
#     def inner(sample):
#         return 2 * class1.pdf(sample) - class2.pdf(sample)
#     return inner


# def plot_roc():
#     with open('dataset.txt') as f:
#         dataset = json.load(f)
#     # Training model
#     class1_samples = np.matrix(dataset['class1']['samples']).T
#     class2_samples = np.matrix(dataset['class2']['samples']).T
#     class1 = mnormal(mean=np.asarray(np.mean(class1_samples, axis=1)).reshape(-1), cov=np.cov(class1_samples))
#     class2 = mnormal(mean=np.asarray(np.mean(class2_samples, axis=1)).reshape(-1), cov=np.cov(class2_samples))
#     g = decide(class1, class2)

#     # Counting TP and FP
#     samples = [(g(sample), 'class1') for sample in dataset['class1']['samples']] + [(g(sample), 'class2') for sample in dataset['class2']['samples']]
#     samples.sort(key=lambda e: e[0], reverse=True)
#     samples = [sample[1] for sample in samples]
#     tp = np.cumsum([sample=='class1' for sample in samples])
#     tp = [i/len(dataset['class1']['samples']) for i in tp]
#     fp = np.cumsum([sample=='class2' for sample in samples])
#     fp = [i/len(dataset['class2']['samples']) for i in fp]

#     # Plot
#     plt.plot(fp, tp)
#     plt.plot([0,1], [0,1], '--')
#     plt.xlabel('False Positive Rate')
#     plt.ylabel('True Positive Rate')
#     plt.savefig('roc.pdf')

