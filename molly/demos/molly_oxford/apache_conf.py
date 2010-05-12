import os.path

def main():
    f, g = open('apache.conf.template'), open('apache.conf', 'w')
    g.write(f.read() % {'root': os.path.abspath('.')})

if __name__ == '__main__':
    main()
