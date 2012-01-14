from werkzeug.routing import Map,Rule, parse_rule

m = Map([
        Rule('/upload<path:f>', endpoint='upload'),
    ])

c = m.bind('example.com')
print(m)

url = c.build('upload', dict(f='foo/bar'))
print url, 'match', c.test(url)

url = c.build('upload', dict(f='/foo/bar'))
print url, 'match', c.test(url)

print [x for x in parse_rule('/upload<path:f>')]