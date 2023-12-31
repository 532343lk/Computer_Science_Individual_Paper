# Computer_Science_Individual_Paper

This code gives the implementation of our version of the MSMP(+) model. We start by extracting model words from the data representation using 2 regexes. Then we create a binary matrix with model words as rows and products as columns. We shorten this matrix using the minhash technique, and then perform LSH to find candidate pairs. Finally, we run a complete linkage hierarchical clustering on the dissimilarity matrix between all products to find teh predicted candidates. 

The code is initialized to run with r=4 rows in the signature matrix split. The parameter (gamma) which dictates how similar keys must be to be considered similar in the similarity calculation of the clustering part is set to 0.15. To switch between our approach (entire code) to MSMP+ (comment out line 175, 179, 180, 181) to MSMP (comment out line 171 upto and including 181), you can simply apply the changes mentioned between brackets. 
You must manually set the number of hash functions to consider. We choose this to be an anti-prime approximately half of the length of all model words. When switching between the models, you should change this number, as the number of models words extracted changes too. The filepath needs to be set accordingly too. 

There are 3 final sets, actual_pairs contains the real pairs, candidate_pairs are the pairs outputted by LSH, and predicted_pairs are the pairs given after clustering. We compute a variety of criteria to measure LSH and clustering performance. 
