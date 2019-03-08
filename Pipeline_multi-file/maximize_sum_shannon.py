from numpy import arange, ndarray, zeros, concatenate, uint64
from math import log10
from pandas import Series, concat


def shannon_index(X: Series):
    H: float = 0.0
    n: int = X.shape[0]
    for count in X.value_counts():
        # calculate proportion of this integer value in the total population of values
        p_i = count / n
        # calculate the Shannon Index (H) given p_i of this value.
        H += p_i * log10(p_i)
    H *= -1
    return H


def make_binary_matrix(X: Series):
    boolean_matrix = zeros((X.shape[0], 8), dtype=uint64)
    for i, row in enumerate(X.iteritems()):
        if row[1] > 0:
            # i is the row in the boolean_matrix
            # j*8 is the left hand bit for this byte in the payload
            # j*8 + 8 is the right hand bit for this byte in the payload
            # e.g. byte index 1 starts at bits 1*8 = 8 to 1*8+8 = 16; [8:16]
            # likewise, byte index 7 starts at bits 7*8 = 56 to 7*8+8 = 64
            # Numpy indexing is non-inclusive of the upper bound. So [0:8] is the first 8 elements
            bin_string = format(row[1], '08b')
            boolean_matrix[i, :] = [x == '1' for x in bin_string]
    return boolean_matrix


def binary_to_int(X: ndarray, tokens: list):
    signals = {}
    for token in tokens:
        # Convert the binary ndarray to a list of string representations of each row
        temp1 = [''.join(str(x) for x in row) for row in X[:, token[0]:token[1] + 1]]
        temp2 = zeros((temp1.__len__(), 1), dtype=uint64)
        # convert each string representation to int
        for i, row in enumerate(temp1):
            temp2[i] = int(row, 2)

        # create an unsigned integer pandas.Series using the time index from this Arb ID's original data.
        signal = Series(temp2[:, 0])
        signals[token] = signal
    return signals


x1 = Series(arange(0, 32, 1))
x1 = concat([x1, x1], axis=0, ignore_index=True)
x1 = concat([x1, x1], axis=0, ignore_index=True)
x1 = concat([x1, x1], axis=0, ignore_index=True)
# x1 = concat([Series(arange(0, 10, 1)), x1], axis=0, ignore_index=True)
# x1 = concat([x1, x1], axis=0, ignore_index=True)
x2 = Series(arange(0, 256, 1))

# print(x1)
# print(shannon_index(x1))
# print(shannon_index(x2))

x1_bin = make_binary_matrix(x1)
x2_bin = make_binary_matrix(x2)

# print(x1_bin)
# print(x2_bin.shape)
x12_bin = concatenate((x1_bin, x2_bin), axis=1)

lower = 0
upper = 15
cutoff = 0
sum_shannon = {}
while cutoff < upper:
    d = binary_to_int(x12_bin, [(0, cutoff), (cutoff+1, 15)])
    this_sum = 0
    for k, v in d.items():
        this_sum += shannon_index(v)
    sum_shannon[cutoff] = this_sum
    cutoff += 1

for k, v in sum_shannon.items():
    print(k, v)
