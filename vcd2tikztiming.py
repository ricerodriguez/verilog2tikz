#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Ernst Blecha, https://github.com/ernstblecha/vcd2tikztiming"
__copyright__ = "Copyright 2018"
__credits__ = ["Sameer Gauria", "Florian Dietachmayr"]
__license__ = "GPL"
__version__ = "0.0.2"
__maintainer__ = "Ernst Blecha"
__email__ = "ernst.blecha@gmail.com"
__status__ = "Prototype"

import os
import sys
import pprint
import tempfile

from Verilog_VCD import parse_vcd, get_endtime
# Verilog_VCD.py version 1.11 taken from
# https://pypi.org/project/Verilog_VCD/#files

pp = pprint.PrettyPrinter(indent=4)
fnames = []

try:
    fn = sys.argv[1]
    fns = fn.split('.')
    vcd = parse_vcd(fn)
except IndexError as err:
    raise err

start = 0
end = get_endtime()
scale = 1000

for f in sys.argv:
    if f.startswith("start="):
        start = 1000*int(f[6:])
        if start > get_endtime():
            start = get_endtime()
        if start < 0:
            start = 0
        if start > end:
            start = end
#        print("start: " + str(start))
    elif f.startswith("end="):
        end = 1000*int(f[4:])
        if end > get_endtime():
            end = get_endtime()
        if end < 0:
            end = 0
        if end < start:
            end = start
#        print("end: " + str(end))
    elif f.startswith("scale="):
        scale = int(f[6:])
        if scale < 0:
            scale = abs(scale)
#        print("scale: " + str(scale))
with open(fns[0] + '_timecodes.tex','w+') as fcodes:
      tcdata = ('\\providecommand\\timeStart{0}\n'
                '\\renewcommand\n'
                '\\timeStart{'+str(start*1./scale)+'}\n'
                '\\providecommand\\timeEnd{0}'
                '\\renewcommand\\timeEnd{'+str(end*1./scale)+'}\n')
      fcodes.writelines(tcdata)

data = {}
# print('vcd is ',vcd)
for d in vcd:
    tv = [(t[0], t[1], i) for i, t in enumerate(vcd[d]['tv'])]
    # print('tv is ',tv)
    results = [(t[0], t[1], t[2]) for t in tv if t[0] > start and t[0] < end]
    # print('results is',results)
    try:
        if results[0][0] > start and results[0][2] > 0:
            results.insert(
                           0, (
                               start,
                               tv[results[0][2] - 1][1],
                               tv[results[0][2] - 1][2]
                              )
                          )
        if results[-1][0] < end and results[-1][2] < tv[-1][2]:
            results.append(
                           (
                            end,
                            tv[results[-1][2] + 1][1],
                            tv[results[-1][2] + 1][2]
                           )
                          )

        u = results[0]
        dv = []
        for v in results[1:]:
            dv.append(
                      (
                       (v[0]-u[0])*1./scale,
                       u[1]
                      )
                     )
            u = v
        dv.append(
                  (
                   (end-u[0])*1./scale,
                   u[1]
                  )
                 )
        name_fix = str(vcd[d]['nets'][0]['name']).replace('_','\_')
        data = {
                **data,
                **dict(
                       [
                        (
                         # vcd[d]['nets'][0]['name'],
                            name_fix,
                         (
                          vcd[d]['nets'][0]['size'],
                          dv
                         )
                        )
                       ]
                      )
               }
    except:
        pass

for d in data:
    s = d + " & "
    for i in data[d][1]:
        if data[d][0] == "1":
            if i[0] == 0:
                s = s + "G"
            elif i[1] == "0":
                s = s + str(i[0]) + "L"
            elif i[1] == "1":
                s = s + str(i[0]) + "H"
            elif i[1] == "z" or i[1] == "Z":
                s = s + str(i[0]) + "Z"
            elif i[1] == "x" or i[1] == "X":
                s = s + str(i[0]) + "X"
            else:
                s = s + str(i[0]) + "U"
        else:
            s = s + str(i[0]) + "D{" + hex(int(i[1], 2)) + "}"
    s = s + " \\\\\n"
    fname = fns[0] + "_" + d + ".dmp"
    fnames.append(fname)
    f = open(fname, "w")
    f.write(s)
    f.close()
bof =  ('\\documentclass{article}\n'
        '\\usepackage[active,tightpage]{preview}\n'
        '\\usepackage{tikz-timing}\n'
        '\\usepackage{fp}\n'
        '\\usepackage{siunitx}\n'
        '%% timingaxis from https://tex.stackexchange.com/questions/67821/tikz-timing-is-there-a-straightforward-way-to-add-a-numbered-time-axis\n'
        '\\providecommand\\timeStart{0}\n'
        '\\newcommand{\\timingaxis}[1][1]{%\n'
        '  \\begin{scope}\n'
        '  \\draw [timing/table/axis] (0,-2*\\nrows+1) -- (\\twidth,-2*\\nrows+1);\n'
        '  \\foreach \\n in {0,#1,...,\\twidth} {\n'
        '    \\draw [timing/table/axis ticks]\n'
        '        (\\n,-2*\\nrows+1+.1) -- +(0,-.2)\n'
        '        node [below,inner sep=2pt] {\\scalebox{.75}{\\tiny\\FPeval\\result{clip(\\timeStart+\\n)}\\num{\\result}}};\n'
        '  }\n'
        '  \\end{scope}\n'
        '}\n'
        '\\tikzset{%\n'
        '    timing/table/axis/.style={->,>=latex},\n'
        '    timing/table/axis ticks/.style={},\n'
        '}\n'
        '\\begin{document}\n'
        '\\begin{preview}\n'
        '  \\begin{tikztimingtable}[xscale=1]\n')
eof = ('\\begin{extracode}\n'
       '\\input{%s_timecodes.tex}\\timingaxis[10]\\relax\n'
       '\\end{extracode}\n'
       '  \\end{tikztimingtable}\n'
       '\\end{preview}\n'
       '\\end{document}\n' % fns[0])

for dmp in fnames:
    line = '\input{%s}\n'%dmp
    bof+=line

try:
    os.remove(fns[0] + '.tmp')
    os.remove(fns[0] + '.tex')
except:
    pass

with open(fns[0] + '.tmp','a+') as template:
    template.writelines(bof)
    template.writelines(eof)

with open(fns[0] + '.tex','w+') as final:
    os.system('latexpand ' + fns[0] + '.tmp > ' + fns[0] + '.tex')

try:
    os.remove(fns[0] + '.tmp')
    os.remove(fns[0] + '_timecodes.tex')
    for dmp in fnames:
        os.remove(dmp)
except:
    pass

