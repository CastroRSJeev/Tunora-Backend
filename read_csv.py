import csv

with open('song_list.csv', mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for i, row in enumerate(reader):
        print(row)
        if i >= 10:
            break
