# Computer_Science_Individual_Paper

The code is initialized to run with r=4 rows in the signature matrix split. The parameter (gamma) which dictates how similar keys must be to be considered similar in the similarity calculation of the clustering part is set to 0.15. To switch between our approach (entire code) to MSMP+ (comment out line 175, 179, 180, 181) to MSMP (comment out line 171 upto and including 181), you can simply apply the changes mentioned between brackets. 
You must manually set the number of hash functions to consider. We choose this to be an anti-prime approximately half of the length of all model words. When switching between the models, you should change this number, as the number of models words extracted changes too. The filepath needs to be set accordingly too. 
