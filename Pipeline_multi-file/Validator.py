from LexicalAnalysis import get_composition_just_tang, merge_tokens_just_composition
from sklearn.model_selection import KFold
from ArbID import ArbID
from numpy import arange, ndarray, zeros, float16, add, divide, argmax, unravel_index


# Threshold parameters used during tokenization.
tokenization_bit_distance:  float = 0.2
tokenize_padding:           bool = True


def alignment_score(mismatch: int, bit_width: int):
    # Alignment Score: 1 - (union-intersection) / (n-1)
    # The range of Alignment Score is 0 (all mismatch) to 1 (all match)
    return float16(1 - mismatch / (bit_width - 1))


def borders(token: tuple, last_index: int):
    if not token[0] == 0:
        if not token[1] == last_index:
            return [token[0]-1, token[1]]
        else:
            return [token[0]-1]
    else:
        if not token[1] == last_index:
            return [token[1]]
    return []


def train_test_alignment_score(tang_a: ndarray, tang_b: ndarray, max_inversion: float, max_merge: float):
    # Note: padding is used as a dummy variable to maintain compatibility with the primary pipeline get_composition()
    comp_a, padding = get_composition_just_tang(tang_a, include_padding=True, max_inversion_distance=max_inversion)
    comp_a = merge_tokens_just_composition(tokens=comp_a, this_tang=tang_a, max_distance=max_merge)
    comp_b, padding = get_composition_just_tang(tang_b, include_padding=True, max_inversion_distance=max_inversion)
    comp_b = merge_tokens_just_composition(tokens=comp_b, this_tang=tang_b, max_distance=max_merge)

    bit_width = len(tang_a)
    id_a_borders = []
    id_b_borders = []

    for token in comp_a:
        # print("\nToken:", token)
        # result = borders(token, bit_width-1)
        # print("\tBorders:", result)
        id_a_borders.extend(borders(token, bit_width-1))
    for token in comp_b:
        # print("\nToken:", token)
        # result = borders(token, bit_width - 1)
        # print("\tBorders:", result)
        id_b_borders.extend(borders(token, bit_width-1))

    id_a_borders = set(id_a_borders)
    id_b_borders = set(id_b_borders)
    # Mismatch set is the symmetric difference: borders where there was a border in only one of the two payloads.
    mismatch_set = id_a_borders.union(id_b_borders) - id_a_borders.intersection(id_b_borders)

    return alignment_score(len(mismatch_set), bit_width)


class Validator:
    def __init__(self,
                 use_j1979:     bool = False,
                 fold_n:        int = 5):
        self.use_j1979:     bool = use_j1979
        self.fold_n:        int = fold_n

    @staticmethod
    # This function allows for pickling just the score matrix and re-creating a Sample object using it later.
    def set_lex_threshold_parameters(sample):
        if sample.avg_score_matrix.shape[0] > 1:
            optimal_setting = argmax(sample.avg_score_matrix)
            optimal_setting = unravel_index(optimal_setting, sample.avg_score_matrix.shape)
            sample.optimal_bit_dist = optimal_setting[0]
            sample.optimal_merge_dist = optimal_setting[1]
        else:
            print("\nSet lex threshold parameters was improperly called for sample " + sample.output_vehicle_dir)

    def k_fold_lex_threshold_selection(self, id_dict: dict, sample):
        list_of_inversion_values = arange(0, 1.01, 0.01)
        list_of_merge_values = arange(0, 1.01, 0.01)
        sample.avg_score_matrix = zeros((len(list_of_inversion_values), len(list_of_merge_values)), dtype=float16)
        number_of_ids_scored: int = 0

        for id_label, arb_id in id_dict.items():  # type: int, ArbID
            if arb_id.static or arb_id.short:
                continue
            this_id_avg_score_matrix = zeros((len(list_of_inversion_values), len(list_of_merge_values)), dtype=float16)

            print("\tID:", id_label, "\tnumber of observed payloads:", arb_id.original_data.shape[0])

            kf = KFold(n_splits=self.fold_n)
            for k, (train, test) in enumerate(kf.split(arb_id.boolean_matrix)):
                score_matrix = zeros((len(list_of_inversion_values), len(list_of_merge_values)), dtype=float16)
                train_tang = arb_id.generate_tang(boolean_matrix=arb_id.boolean_matrix[train])
                test_tang = arb_id.generate_tang(boolean_matrix=arb_id.boolean_matrix[test])

                for m, i in enumerate(list_of_inversion_values):
                    for n, j in enumerate(list_of_merge_values):
                        score_matrix[m, n] = train_test_alignment_score(train_tang, test_tang, i, j)
                this_id_avg_score_matrix = add(this_id_avg_score_matrix, score_matrix)
            this_id_avg_score_matrix = divide(this_id_avg_score_matrix, self.fold_n)
            sample.avg_score_matrix = add(sample.avg_score_matrix, this_id_avg_score_matrix)
            number_of_ids_scored += 1
        sample.avg_score_matrix = divide(sample.avg_score_matrix, number_of_ids_scored)
        self.set_lex_threshold_parameters(sample)
