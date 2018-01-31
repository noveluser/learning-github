#!/usr/local/bin/python2.7      
#coding=utf-8


b = ['Active count']
with open('/data/cyy928/logs/play_status.log', 'r') as f:
    a = []
    lines = f.readlines()
    print(lines[0])
    for x in lines:
        if x.startswith('a'):
            a.extend([x.strip().split()[0], lines.index(x),])
			print a
    for i in b[:-1]:
        if i in a:
            c = a.index(i)
            print ''.join(lines[a[c+1]:a[c+3]])
    if b[-1] == a[-2]:
        print ''.join(lines[a[int(a.index(b[-1]) + 1)]:])
    else:
        print ''.join(lines[a[int(a.index(b[-1])) + 1]:a[int(a.index(b[-1])) + 3]])