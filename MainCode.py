import itertools
import json
import numpy as np
from scipy.spatial.distance import squareform
import re
import random
from nltk import ngrams
from scipy.cluster.hierarchy import linkage, fcluster

file_path = "//Users/lorenzkremer/Documents/TVs-all-merged.json"


def load_dataset(file_path, num_keys=None):
    with open(file_path) as f:
        data = json.load(f)

    if num_keys is not None:
        # Get the first num_keys keys
        selected_keys = list(data.keys())[:num_keys]

        # Create a new dictionary with the selected keys and their values
        new_data = {}
        for key in selected_keys:
            new_data[key] = data[key]
        return new_data
    else:
        return data


# function to load bootstrap data
def load_dataset_subset(file_path, num_keys=None):
    with open(file_path) as f:
        data = json.load(f)

    selected_keys = random.sample(list(data.keys()), num_keys)

    new_data = {}
    for key in selected_keys:
        new_data[key] = data[key]

    return new_data


def calculate_qgrams_similarity(product1, product2, q, gamma):
    keys1 = list(product1.keys())
    keys2 = list(product2.keys())
    keys1.remove("shop")  # these are added in the copy_data for simplicity, but aren't in the original data
    keys2.remove("shop")
    total_similarity = 0
    total_weight = 0
    key_pairs = []
    brand1 = ""
    brand2 = ""
    sameBrand = True
    sameShop = False

    # check whether brands are same
    for key1 in keys1:
        if "Brand" in key1:
            brand1 = product1[key1]
    for key2 in keys2:
        if "Brand" in key2:
            brand2 = product2[key2]

    if brand1 != "" and brand2 != "":
        if brand1 != brand2:
            sameBrand = False

    # check whether shop is the same
    if product1["shop"] == product2["shop"]:
        sameShop = True

    if sameBrand and not sameShop:
        for key1 in keys1:
            for key2 in keys2:
                qgrams_1 = list(ngrams(key1, q))
                qgrams_2 = list(ngrams(key2, q))
                intersection = len(set(qgrams_1).intersection(qgrams_2))
                union = len(set(qgrams_1).union(qgrams_2))
                similarity = intersection / union
                if similarity > gamma:
                    key_pairs.append((key1, key2, similarity))

        for pair in key_pairs:
            value1 = product1[pair[0]]
            value2 = product2[pair[1]]
            weight = pair[2]
            total_weight += weight
            qgrams_val_1 = list(ngrams(value1, q))
            qgrams_val_2 = list(ngrams(value2, q))
            intersect = len(set(qgrams_val_1).intersection(qgrams_val_2))
            uni = len(set(qgrams_val_1).union(qgrams_val_2))
            sim = 0
            if uni != 0:
                sim = intersect / uni
            total_similarity += (weight * sim)

    avg_similarity = 0
    if total_weight > 0:
        avg_similarity = total_similarity / total_weight

    return avg_similarity


# Function to create a similarity matrix
def create_similarity_matrix(products_data, candidate_pairs, q, gamma):  # copy_data
    n_products = len(products_data)
    similarity_matrix = np.zeros((n_products, n_products))

    for i in range(len(products_data)):
        similarity_matrix[i, i] = 1

    for pair in candidate_pairs:
        similarity_matrix[pair[0], pair[1]] = similarity_matrix[pair[1], pair[0]] = \
            calculate_qgrams_similarity(products_data[pair[0]], products_data[pair[1]], q, gamma)

    return similarity_matrix


def hierarchical_clustering(similarity_matrix, epsilon, method='complete'):
    dissimilarity_matrix = 1 - similarity_matrix
    condensed_distance = squareform(dissimilarity_matrix)
    linkage_matrix = linkage(condensed_distance, method=method)
    clusters = fcluster(linkage_matrix, t=epsilon, criterion='distance')
    cluster_product_mapping = {}

    prod_number = 0
    for i in range(len(clusters)):
        if clusters[i] not in cluster_product_mapping:
            cluster_product_mapping[clusters[i]] = []
        cluster_product_mapping[clusters[i]].append(prod_number)
        prod_number += 1

    predicted_pairs = set()
    for products_in_cluster in cluster_product_mapping.values():
        if len(products_in_cluster) > 1:
            predicted_pairs.update(
                (item1, item2) if item1 < item2 else (item2, item1) for item1 in products_in_cluster for item2 in
                products_in_cluster if item1 != item2)

    return predicted_pairs


full_data = load_dataset(file_path)
regex_title = r"[a-zA-Z0-9]*(([0-9]+[^0-9, ]+)|([^0-9, ]+[0-9]+))[a-zA-Z0-9]*"
regex_decimal = r'^\d+\.\d+[a-zA-Z]*$'
num_bootstraps = 10
for gamma in [0.15]:
    fraction_of_comparison_MSMP = []
    pair_quality_MSMP = []
    pair_completeness_MSMP = []
    F1_scores_MSMP = []
    F1_star_scores_MSMP = []
    for r_row in [4]:
        F1_scores = []
        F1_star_scores = []
        frac_of_comparisons = []
        pair_qualities = []
        pair_completenesses = []
        for B in range(num_bootstraps):
            data = load_dataset_subset(file_path, int(0.63 * len(full_data)))
            product_model_words_list = []  # list which contains set of model words per product
            all_model_words = set()  # set of all model words across all products
            productCount = 0
            for i in data:
                for j in range(len(data[i])):
                    title = data[i][j]["title"]
                    words = title.split()
                    model_words = {word for word in words if re.match(regex_title, word)}

                    items_list = list(data[i][j]["featuresMap"].values())
                    for k in range(len(items_list)):
                        subwords = items_list[k].split()
                        decimal_words = [subword for subword in subwords if re.match(regex_decimal, subword)]
                        model_words_values = [value for value in subwords if re.match(regex_title, value)]
                        if len(decimal_words) > 0:
                            for l in range(len(decimal_words)):
                                model_words.add(decimal_words[l])
                        if len(model_words_values) > 0:
                            for w in range(len(model_words_values)):
                                model_words.add(model_words_values[w])

                    product_model_words_list.append(model_words)
                    for model_word in model_words:
                        all_model_words.add(model_word)

            num_rows = len(all_model_words)
            num_cols = sum(len(data[i]) for i in data)
            matrix = np.zeros((num_rows, num_cols), dtype=int)

            data_copy_index = 0
            copy_data = {}  # make copy of data to make indexation easier
            for i in data:
                for j in range(len(data[i])):
                    copy_data[data_copy_index] = data[i][j]["featuresMap"]
                    copy_data[data_copy_index]["shop"] = data[i][j]["shop"]
                    data_copy_index += 1

            for col, product_set in enumerate(product_model_words_list):
                for row, model_word in enumerate(all_model_words):
                    if model_word in product_set:
                        matrix[row, col] = 1

            p = 3359  # random prime larger than number of hash functions
            hash_functions = []
            for i in range(int(2520)):  # choose this to be an anti-prime
                hash_func = [random.randint(1, 1000), random.randint(1, 1000)]
                hash_functions.append(hash_func)
            num_hash_funcs = len(hash_functions)
            signature_matrix = np.full((num_hash_funcs, num_cols), np.inf)  # 2520x1624

            for row in range(num_rows):
                hash_values = []
                for hash in range(num_hash_funcs):
                    a, b = hash_functions[hash]
                    hash_value = (a + b * row) % p
                    hash_values.append(hash_value)
                for column in range(num_cols):
                    if matrix[row, column] == 1:
                        for index, val in enumerate(hash_values):
                            if val < signature_matrix[index, column]:
                                signature_matrix[index, column] = val

            num_rows_sign = signature_matrix.shape[0]
            num_cols_sign = signature_matrix.shape[1]

            r = r_row
            b = int(num_hash_funcs / r_row)

            candidate_pairs = set()  # output of LSH. Set of all candidate pairs where pairs are lists of 2 integers.
            # ex. [1,2]
            list_of_hash_buckets = []  # list of dictionaries. A dictionary can be seen as a collection of buckets

            # hash bands to buckets. items are only hashed to same bucket if they're exactly equal in that band
            for band in range(b):
                hash_buckets = {}  # each bucket contains keys (hash-values) and values (column indices which were
                # hashed to said bucket)
                for column in range(num_cols):
                    hash = ""
                    for row in range(band * r, (band + 1) * r):
                        hash = hash + str(signature_matrix[row, column])
                    if hash not in hash_buckets:
                        hash_buckets[hash] = []
                    hash_buckets[hash].append(column)
                list_of_hash_buckets.append(hash_buckets)

            # find candidate pairs
            for band, buckets_in_band in enumerate(list_of_hash_buckets):
                for bucket, items_in_bucket in buckets_in_band.items():
                    if len(items_in_bucket) > 1:
                        candidate_pairs.update(
                            (item1, item2) if item1 < item2 else (item2, item1) for item1 in items_in_bucket for item2
                            in
                            items_in_bucket if item1 != item2)

            # finds actual duplicates
            modelID_dict = {}
            index = 0
            for i in data:
                for j in range(len(data[i])):
                    modelID = data[i][j]["modelID"]
                    if modelID not in modelID_dict:
                        modelID_dict[modelID] = []
                    modelID_dict[modelID].append(index)
                    index += 1

            actual_pairs = set()
            for model_indices in modelID_dict.values():
                # Use itertools.combinations to get all possible pairs
                pairs = list(itertools.combinations(model_indices, 2))
                actual_pairs.update(pairs)

            sim_matrix = create_similarity_matrix(copy_data, candidate_pairs=candidate_pairs, q=3, gamma=gamma)
            predicted_pairs = hierarchical_clustering(sim_matrix, epsilon=0.99)

            TP = len(predicted_pairs.intersection(actual_pairs))
            n_prods = len(signature_matrix[0])
            fraction_comparisons = len(candidate_pairs) / (n_prods * (n_prods - 1) / 2)
            frac_of_comparisons.append(fraction_comparisons)
            FP = len(predicted_pairs.difference(actual_pairs))
            FN = len(actual_pairs.difference(predicted_pairs))
            pair_quality = len(candidate_pairs.intersection(actual_pairs)) / len(candidate_pairs)
            pair_completeness = len(candidate_pairs.intersection(actual_pairs)) / len(actual_pairs)
            pair_qualities.append(pair_quality)
            pair_completenesses.append(pair_completeness)
            precision = TP / (TP + FP)
            recall = TP / (TP + FN)
            if precision != 0 and recall != 0:
                F1 = 2 * precision * recall / (precision + recall)
            else:
                F1 = 0
            if pair_quality != 0 and pair_completeness != 0:
                F1_star = 2 * pair_quality * pair_completeness / (pair_quality + pair_completeness)
            else:
                F1_star = 0
            F1_scores.append(F1)
            F1_star_scores.append(F1_star)
        fraction_of_comparison_MSMP.insert(0, np.mean(frac_of_comparisons))
        pair_quality_MSMP.insert(0, np.mean(pair_qualities))
        pair_completeness_MSMP.insert(0, np.mean(pair_completenesses))
        F1_scores_MSMP.insert(0, np.mean(F1_scores))
        F1_star_scores_MSMP.insert(0, np.mean(F1_star_scores))
    print("All averaged fractions of comparisons: ", fraction_of_comparison_MSMP)
    print("All averaged pair qualities: ", pair_quality_MSMP)
    print("All averaged pair completenesses: ", pair_completeness_MSMP)
    print("All averaged F1 scores: ", F1_scores_MSMP)
    print("All averaged F1_star scores: ", F1_star_scores_MSMP)

