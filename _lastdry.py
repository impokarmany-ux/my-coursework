import glob,os
f=sorted(glob.glob('logs/*dry.log'),key=os.path.getmtime)[-1]
for l in open(f,encoding='utf-8'):
    if 'СУХО] seq' in l and ('Alliance' in l or 'unSub' in l or 'Ruin' in l) or 'СТОП' in l or 'готово' in l: print(l.rstrip()[:160])
