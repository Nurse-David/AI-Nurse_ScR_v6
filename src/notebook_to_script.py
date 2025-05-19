import json, sys, pathlib

if len(sys.argv) != 3:
    print('Usage: notebook_to_script.py <input.ipynb> <output.py>')
    sys.exit(1)

inp = pathlib.Path(sys.argv[1])
outp = pathlib.Path(sys.argv[2])

with inp.open('r', encoding='utf-8') as f:
    nb = json.load(f)

with outp.open('w', encoding='utf-8') as f:
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            f.write('# --- Cell ---\n')
            for line in cell.get('source', []):
                f.write(line)
            f.write('\n\n')
