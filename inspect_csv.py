import csv
import json

try:
    with open('song_list.csv', mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = []
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 4:
                break
        
        info = {
            "headers": headers,
            "sample_rows": rows
        }
        
    with open('csv_data.json', 'w') as f:
        json.dump(info, f, indent=4)
except Exception as e:
    with open('csv_error.txt', 'w') as f:
        f.write(str(e))
