# ShortURL (https://github.com/delight-im/ShortURL)
# Copyright (c) delight.im (https://www.delight.im/)
# Licensed under the MIT License (https://opensource.org/licenses/MIT)
from pymongo import MongoClient
import datetime
import time

class ShortURL:
    """
    ShortURL: Bijective conversion between natural numbers (IDs) and short strings

    ShortURL.encode() takes an ID and turns it into a short string
    ShortURL.decode() takes a short string and turns it into an ID

    Features:
    + large alphabet (51 chars) and thus very short resulting strings
    + proof against offensive words (removed 'a', 'e', 'i', 'o' and 'u')
    + unambiguous (removed 'I', 'l', '1', 'O' and '0')

    Example output:
    123456789 <=> pgK8p
    """

    _alphabet = '23456789bcdfghjkmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ-_'
    _base = len(_alphabet)

    def encode(self, number):
        string = ''
        while(number > 0):
            string = self._alphabet[number % self._base] + string
            number //= self._base
        return string

    def decode(self, string):
        number = 0
        for char in string:
            number = number * self._base + self._alphabet.index(char)
        return number

    
class Cantor:
    def dec_to_cant(x):
        n = 1
        y = x
        a = []
        while y:
            a += [y % (n + 1)]
            y = (y - a[-1]) // (n + 1)
            n += 1
        return a
    
    def cant_to_dec(a):
        x = 0
        n = len(a)
        for i in range(n, 0, -1):
            x = x + a[i-1]
            x *= i
        return x
    
def rotate(l, n):
    return l[-n:] + l[:-n]

# Map int x to another int y
def f(x):
    return Cantor.cant_to_dec(rotate(Cantor.dec_to_cant(x), N))

# Find the int y that f(y) = x
def finv(x):
    return Cantor.cant_to_dec(rotate(Cantor.dec_to_cant(x), -N))

client = MongoClient()
db = client.shortenurl
N = 7
count = round(time.time() * 1000) % (24*3600*1000)    # start from random number
LIFE = datetime.timedelta(seconds=5)

def encodeUrl(url, permanent=False):
    global count
    url = str(url)
    cursor = list(db.urlmap.find({'url': url}))
    life = LIFE if not permanent else datetime.timedelta(years=999)
    if cursor:
        surl = cursor[0]['_id']
        db.urlmap.update({'_id': surl}, {'$set': {'delete_at': datetime.datetime.now() + life}})
    else:
        surl = ShortURL().encode(f(count))
        while True:
            count += 1
            try:
                db.urlmap.insert({'_id': surl, 'url': url, 'delete_at': datetime.datetime.now() + life})
            except pymongo.errors.DuplicateKeyError as e:
                print(e)
                continue
            else:
                break
    return surl

def decodeUrl(surl):
    cursor = list(db.urlmap.find({'_id': surl}))
    if cursor:
        if cursor[0]['delete_at'] <= datetime.datetime.now() + LIFE:
            db.urlmap.update({'_id': surl}, {'$set': {'delete_at': datetime.datetime.now() + LIFE}})
        return cursor[0]['url']
    else:
        return None

def clear():
    return db.urlmap.delete_many({'delete_at':{'$lt': datetime.datetime.now()}}).deleted_count
