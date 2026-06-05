import json
import os
import glob

notebooks = glob.glob('prediction/**/*.ipynb', recursive=True)

for nb in notebooks:
    if '.ipynb_checkpoints' in nb:
        continue
    with open(nb, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    modified = False
    for cell in data.get('cells', []):
        if cell.get('cell_type') == 'code':
            source = cell.get('source', [])
            new_source = []
            for line in source:
                if '/Users/oguzhanerbil/Documents/Repolarım/food-health-predictor/data/' in line:
                    line = line.replace('/Users/oguzhanerbil/Documents/Repolarım/food-health-predictor/data/', '../../data/')
                    modified = True
                new_source.append(line)
            cell['source'] = new_source
            
    if modified:
        with open(nb, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print(f"Fixed paths in {nb}")
