import csv
csv_file = open("./list.csv", encoding="utf_8")
f = csv.reader(csv_file)
header = next(f)
buttonlist = [str(row[2]) for row in f]

print(buttonlist)