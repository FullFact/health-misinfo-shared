# place to store/access manually written prompts & templates
# Maybe add 'physical or mental health'

HEALTH_HARM_PROMPT = """
            Your task is to help people quickly understand a video transcript and find the most harmful claims about health being made. 
            You should only consider sentences that are about health, medicine, public health or hospitals. 
            You should estimate the potential harm of the claims.
            
            You will analyse the text delimited by triple backticks as follows.

            Perform the following actions.
            1 - Find up to 5 claims that are the most specific, informative and verifiable. Ignore sentences that are not directly about health. 
            2 - Choose claims that may lead to harm to health if they are believed. This includes claims made without any scientific evidence to support them 
            as well as claims that have a direct harm on someone's health or may harm public health.
            3 - Explain why each claim is likely to cause harm.
            

            Return a list of JSON format output as follows:
            [
                {
                    "claim": <claims being made in the sentence>,
                    "explain": <explain why this sentence is harmful or misleading>,
                    "sentence": <original, unedited text of the sentence>,
                }
            ]
            Re-write the output and return nothing except correctly formatted JSON.
            """

HEALTH_TRAINING_PROMPT = """
            Your task is to help people quickly understand a video transcript and find the most harmful claims about health being made. 
            You should only consider claims that are on topics like health, medicine, personal health, public health, drugs, treatments or hospitals. 
            You should estimate the potential harm of the claims.
            
            You will analyse the text delimited by triple backticks as follows.

            Perform the following actions.
            1 - Find up to 5 claims that are the most specific, informative and verifiable. Ignore sentences that are not directly about health. 
            2 - Choose claims that may lead to harm to health if they are believed. This includes claims made without any scientific evidence to support them 
            as well as claims that have a direct harm on someone's health or may harm public health.
            3 - If all the claims are accurate or harmless, give the output "seems legit". Otherwise list the harmful claim as output.
            

            Return a list of JSON format output as follows:
            [
                {
                    "claim": <harmful claims being made in the sentence or the phrase "seems legit" if all claims are good>,
                }
            ]
            Re-write the output and return nothing except correctly formatted JSON.
            """

# output will be like:
# [{'claim': 'Saffron is as effective as Prozac in treating symptoms of depression.', 'explanation': 'high harm'},
#  {'claim': 'another claim', 'explanation': 'nothing to check'}]
HEALTH_TRAINING_EXPLAIN_PROMPT = """
            Your task is to help people quickly understand a video transcript and find the most harmful claims about health being made. 
            You should only consider claims that are on topics like health, medicine, personal health, public health, drugs, treatments or hospitals. 
            You should estimate the potential harm of the claims.
            
            You will analyse the text delimited by triple backticks as follows.

            Perform the following actions.
            1 - Find up to 5 claims that are the most specific, informative and verifiable. Ignore sentences that are not directly about health. 
            2 - Choose claims that may lead to harm to health if they are believed. This includes claims made without any scientific evidence to support them 
            as well as claims that have a direct harm on someone's health or may harm public health.
            3 - Explain why the claim is important using one of these labels: "high harm", "low harm", "citation", "nothing to check", "hedged claim".
                Give the explanation "high harm" if the claim is likely to cause serious injury.
                Give the explanation "low harm" if the claim is likely to cause minor injury.
                Give the explanation "citation" if the claim cites scientific work in a misleading way.
                Give the explanation "nothing to check" if the claim is true or harmless or cannit be understood.
                Give the explanation "hedged claim" if the claim is vague or imprecise.    
            4 - Return a list of JSON format output as follows:
            [
                {
                    "claim": <claim being made in the sentence>,
                    "explanation": <one of these labels "high harm", "low harm", "citation", "nothing to check", "hedged claim">
                }
            ]
            Re-write the output and return nothing except correctly formatted JSON.
"""


HEALTH_CLAIM_PROMPT = """
            Your task is to process a video transcript and find any claims made about health. 
            Give the details if a health claim has been made.
            
            Instructions:

            You should only consider claims that are on health topics including  personal health, public health, medicine, mental health, drugs, treatments or hospitals. 
            
            You will analyse the text delimited by triple backticks as follows.

            Find up to 5 claims that are the most specific and informative. 
            Ignore sentences that are not directly about some aspect of health. 
            Ignore sentences that make vague statements or are about someone's individual and personal experiences.

            Return a list of JSON format output as follows:
            [
                {
                    "claim": <claims being made in the sentence>,
                    "sentence": <original, unedited text of the sentence>,
                }
            ]
            Return nothing except a correctly formatted JSON list.
            """
