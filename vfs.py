import os, struct
import itertools

class Block():
    def __init__(self, name, offset=None, length=None, data=None):
        self.name = name
        self.offset = offset
        if length is None and data is not None:
            self.length = len(data)
        else:
            self.length = length
        self._data = data
    
    @property
    def data(self):
        return self._data

    def set_data(self, v):
        self._data = v

    def write(self, f):
        assert self._data is not None
        f.seek(self.offset, os.SEEK_SET)
        f.write(self._data)

class StreamBlock():
    def __init__(self, block, table):
        self.block = block
        self.table = table
        self.offset = 0

    def __iter__(self):
        return self

    def __len__(self):
        return self.block.length

    def next(self):
        if self.offset < self.block.length:
            d = self.table.read(self.block, offset=self.offset, length=64*1024)
            self.offset += len(d)
            return d
        raise StopIteration()

class Index(Block):
    def __init__(self, name, offset=None, length=None, data=None):
        Block.__init__(self, name, offset, length, data)
        self.dict = {}

    @staticmethod
    def unpack(v):
        start = 0
        while start + 12 < len(v):
            name_length, = struct.unpack_from('L', v, start)
            if name_length == 0:
                break
            fmt = '%dsLL' % name_length
            name, offset, length = struct.unpack_from(fmt, v, start + 4)
            start += 4 + struct.calcsize(fmt)

            yield name, offset, length

    def set_data(self, v):
        for name, offset, length in Index.unpack(v):
            self.add(Block(name, offset, length))
            
    def write(self, f):
        s = ''
        for k, b in self.dict.iteritems():
            fmt = 'L%dsLL' % len(k)
            d = struct.pack(fmt, len(k), k, b.offset, b.length)
            s += d
        if len(s) < self.length:
            s += str('\0' * (self.length - len(s)))
        f.seek(self.offset, os.SEEK_SET)
        f.write(s)
        
    def add(self, b):
        self.dict[b.name] = b

class Table():
    def __init__(self, filename):
        self.offset = 0
        self.changed = False
        
        self.index = Index('_index', offset=0, length=1024)
        
        try:
            self.file = open(filename, 'r+b')
            self.read(self.index)
        except IOError,e:
            self.file = open(filename, 'w+b')
        
    def __del__(self):
        if self.changed:
            self.write(self.index)
        self.file.close()

    def next_offset(self):
        last_offset = self.index.offset + self.index.length
        for k, v in self.index.dict.iteritems():
            if v.offset >= last_offset:
                last_offset = v.offset + v.length
        # print 'last_offset', last_offset
        return last_offset
        
    def create(self, name, data):
        self.changed = True
        b = Block(name, data=data, offset=self.next_offset())
        self.index.add(b)
        return b
    
    def find(self, name):
        return self.index.dict.get(name)
        
    def write(self, b):
        b.write(self.file)
        
    def read(self, b, offset=0, length=0):
        self.file.seek(b.offset + offset, os.SEEK_SET)
        if length == 0:
            left = b.length - offset
        else:
            left = min(b.length, length)
        buf = ''
        while left > 0:
            x = self.file.read(left)
            if len(x) == 0:
                break
            left -= len(x)
            buf += x
        
        b.set_data(buf)
        return buf
    
    def readdir(self, name):
        # filename, name      left
        # /foo      /f/    F
        # /foo/a/b  /foo/  T  a/b
        
        assert name.endswith('/')
        ns = set()
        for f in itertools.ifilter(lambda x:x.startswith(name), self.index.dict.keys()):
            left = f[len(name):]
            first_splash = f.find('/', len(name))
            # print '>> ', f, '\t', name, left, first_splash
            if first_splash != -1:
                ns.add(f[len(name):first_splash])
        return ns

    def readfile(self, name):
        # filename, name        left
        # /foo      /f/      F
        # /foo/a/b  /foo/    F  a/b
        # /foo/a/b  /foo/a/  T  b
        
        assert name.endswith('/')
        def f(x):
            if not x.startswith(name):
                return False
            left = x[len(name):]
            return left.find('/') == -1
        
        return itertools.ifilter(f, self.index.dict.keys())
        
    def dump(self):
        print self.index.name, (self.index.offset, self.index.length)
        for k,b in self.index.dict.iteritems():
            print k, (b.offset, b.length)

if __name__ == '__main__':
    if not os.path.exists('user.db'):
        t = Table('user.db')
        
        t.write(t.create('/foo/file1', 'efg'))
        t.write(t.create('/foo/file2', 'efg'))
        t.write(t.create('/foo/c/file', 'efg'))
        t.write(t.create('/foo/d/file', 'efg'))
        
        t.dump()

        
        
        
    else:
        t = Table('user.db')
        t.dump()

        assert t.read(t.find('/foo/file1'), offset=0, length=1) == 'e'
        assert t.read(t.find('/foo/file1'), offset=0, length=2) == 'ef'
        assert t.read(t.find('/foo/file1'), offset=1, length=2) == 'fg'

        bi = StreamBlock(t.find('/foo/file1'), t)
        assert [i for i in bi] == ['efg']
        
        print '\nreaddir /', '-' * 20
        for i in t.readdir('/'):
            print i
            
        print '\nreaddir /foo/', '-' * 20
        for i in t.readdir('/foo/'):
            print i
            
        print '\nreadfile /foo/', '-' * 20
        for i in t.readfile('/foo/'):
            print i
        print '\nreadfile /foo/c/', '-' * 20
        for i in t.readfile('/foo/c/'):
            print i
    del t