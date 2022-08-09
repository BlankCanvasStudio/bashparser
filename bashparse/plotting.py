import bashparse, metric
import matplotlib.pyplot as plt

files = []  # specify you files in here
plotting_values = []  # This should remain empty


for FILE in files:
    nodes = bashparse.parse(open(FILE).read())
    raw_score = metric.calculate_raw_file_score(nodes)
    weighted_score = metric.calculate_weighted_file_score(nodes)
    hashed_raw_score = metric.calculate_raw_hashing_score(nodes)
    hashed_weighted_score = metric.calculate_weighted_hasing_score(nodes)

    plotting_values += [ weighted_score ]


plotting_values.sort()

x_axis = list(range(1, len(plotting_values)+1))

plt.plot(x_axis, plotting_values, marker="o")
plt.ylabel('Complexity')
plt.xlabel('Script Number')
plt.xticks(x_axis, x_axis)  # A hysterical way to make sure x axis is ints only
plt.show()