import json

nb_path = 'prediction/analiz1/data_cleaning.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for cell in data.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        new_source = []
        modified = False
        for i, line in enumerate(source):
            if 'unique_values = data[column].unique()' in line:
                pass
            if 'unique_values_str = sorted(list(unique_values))' in line:
                line = line.replace('sorted(list(unique_values))', 'sorted([str(x) for x in unique_values])')
                modified = True
            new_source.append(line)
        if modified:
            cell['source'] = new_source

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print("Fixed sorting error in notebook.")
