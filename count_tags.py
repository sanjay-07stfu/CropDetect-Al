import codecs
path = r"c:\Users\yedag\OneDrive\Desktop\new project\templates\history.html"
lines = codecs.open(path, 'r', 'utf-8', 'replace').read().splitlines()
for i, l in enumerate(lines, 1):
    if '{%' in l:
        print(i, l.strip())
