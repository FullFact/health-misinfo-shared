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

# The training prompt ofr multi-label evaluation.
HEALTH_TRAINING_MULTI_LABEL_PROMPT = """           
            Your task is to help people quickly understand a video transcript and find the most harmful claims about health being made. 
            You should only consider claims that are on topics like health, medicine, personal health, public health, drugs, treatments or hospitals. 
            You should estimate the potential harm of the claims.
                        
            You will analyse the text delimited by triple backticks as follows.

            Perform the following actions.
            1 - Find up to 5 claims that are the most specific, informative and verifiable. Ignore sentences that are not directly about health. 
            2 - Choose claims that may lead to harm to health if they are believed. This includes claims made without any scientific evidence to support them as well as claims that have a direct harm on someone's health or may harm public health.
            3 - Give the claim 5 different labels according to the following rules:

                Label 1: Understandability.
                    Give the label "understandable" if the meaning of the claim is clear and can be understood.
                    Give the label "vague" if there could be a small amount of doubt in the meaning of the claim.
                    Give the label "not understandable" if the meaning of the claim is not clear and cannot be understood.

                Label 2: Type of claim.
                    Give the label "opinion" if the claim is an individual's opinion.
                    Give the label "personal" if the claim is about a specific individual.
                    Give the label "citation" if the claim refers to a study, scientific research, evidence or similar.
                    Give the label "hedged claim" if the claim stops short of being definitive, by saying using words like "can" or "may", or is about a link as opposed to a definitive cause and effect.
                    Give the label "statement of fact" if the claim is stating something as a fact without opinion, qualification, or reference to research of any kind.
                    Give the label "advice/recommendation" if the claim purports to give medical advice.
                    Give the label "not a claim" if the sentence cannot be interpreted as a claim.

                Label 3: Type of medical claim.
                    Give the label "symptom" if the claim refers to a symptom of a condition.
                    Give the label "cause/effect" if the claim refers to something which causes a condition.
                    Give the label "correlation" if the claim refers to a link or correlation between two things.
                    Give the label "prevention" if the claim refers to a way to prevent the onset of a condition.
                    Give the label "treatment/cure" if the claim refers to a treatment or cure for a condition.
                    Give the label "outcome" if the claim refers to the likely outcome of a condition or a recovery time.
                    Give the label "statistics" if the claim refers to a numerical statistic around the health of a group, prevalance of a condition, frequency of an outcome, or waiting lists and other statistics on hospitals, GPs and medical staff.
                    Give the label "not medical" if the claim does not appear to be about anything medical.

                Label 4: Support.
                    Give the label "uncontroversial statement" if the claim appears to be agreed upon by reputable and peer-reviewed journals, textbooks and individuals.
                    Give the label "disputed claim" if there appears to be debate around this claim.
                    Give the label "widely discredited" if reputable and peer-reviewed journals, textbooks and individuals have dismissed or disproved the claim.
                    Give the label "novel claim" if the claim appears not to have been made before.
                    Give the label "can't tell" if it is not clear which of the labels above applies.

                Label 5: Harm.
                    Give the label "high harm" if believing this claim is likely to directly cause serious medical harm to individuals or groups.
                    Give the label "some harm" if believing this claim is likely to directly cause a limited amount of harm to some individuals.
                    Give the label "low harm" if believing this claim is likely to directly cause a only a small amount of harm.
                    Give the label "indirect harm" if believing the claim is likely to cause harm by leading them not to seek legitimate advice or treatment.
                    Give the label "harmless" if beleiving this claim is unlikely to cause any harm to an individual.
                    Give the label "can't tell" if the potential harm of the claim cannot be determined.


            4 - Return a list of JSON format output as follows:
                        [
                            {
                                "claim": <claim being made in the sentence>,
                                "labels":
                                    {
                                        "understandability": <one of these labels: "understandable", "not understandable">,
                                        "type_of_claim": <one of these labels: "statement of fact", "advice/recommendation", "opinion", "personal", "citation", "hedged claim", "not a claim">,
                                        "type_of_medical_claim": <one of these labels: "symptom", "cause/effect", "correlation", "prevention", "statistics", "treatment/cure", "outcome", "not medical">,
                                        "support": <one of these labels: "uncontroversial statement", "disputed claim", "widely discredited", "novel claim", "can't tell">,
                                        "harm": <one of these labels: "high harm", "low harm", "some harm", "harmless", "indirect harm", "can't tell">,
                                    }
                            }
                        ]
                Re-write the output and return nothing except correctly formatted JSON.
"""

# The inference prompt also asks the model to give a "summary"
HEALTH_INFER_MULTI_LABEL_PROMPT = """           
            Your task is to help people quickly understand a video transcript and find the most harmful claims about health being made. 
            You should only consider claims that are on topics like health, medicine, personal health, public health, drugs, treatments or hospitals. 
            You should estimate the potential harm of the claims.
                        
            You will analyse the text delimited by triple backticks as follows.

            Perform the following actions.
            1 - Find up to 5 claims that are the most specific, informative and verifiable. Ignore sentences that are not directly about health. 
            2 - Choose claims that may lead to harm to health if they are believed. This includes claims made without any scientific evidence to support them as well as claims that have a direct harm on someone's health or may harm public health.
            3 - Give the claim 5 different labels according to the following rules:

                Label 1: Understandability.
                    Give the label "understandable" if the meaning of the claim is clear and can be understood.
                    Give the label "vague" if there could be a small amount of doubt in the meaning of the claim.
                    Give the label "not understandable" if the meaning of the claim is not clear and cannot be understood.

                Label 2: Type of claim.
                    Give the label "opinion" if the claim is an individual's opinion.
                    Give the label "personal" if the claim is about a specific individual.
                    Give the label "citation" if the claim refers to a study, scientific research, evidence or similar.
                    Give the label "hedged claim" if the claim stops short of being definitive, by saying using words like "can" or "may", or is about a link as opposed to a definitive cause and effect.
                    Give the label "statement of fact" if the claim is stating something as a fact without opinion, qualification, or reference to research of any kind.
                    Give the label "advice/recommendation" if the claim purports to give medical advice.
                    Give the label "not a claim" if the sentence cannot be interpreted as a claim.

                Label 3: Type of medical claim.
                    Give the label "symptom" if the claim refers to a symptom of a condition.
                    Give the label "cause/effect" if the claim refers to something which causes a condition.
                    Give the label "correlation" if the claim refers to a link or correlation between two things.
                    Give the label "prevention" if the claim refers to a way to prevent the onset of a condition.
                    Give the label "treatment/cure" if the claim refers to a treatment or cure for a condition.
                    Give the label "outcome" if the claim refers to the likely outcome of a condition or a recovery time.
                    Give the label "statistics" if the claim refers to a numerical statistic around the health of a group, prevalance of a condition, frequency of an outcome, or waiting lists and other statistics on hospitals, GPs and medical staff.
                    Give the label "not medical" if the claim does not appear to be about anything medical.

                Label 4: Support.
                    Give the label "uncontroversial statement" if the claim appears to be agreed upon by reputable and peer-reviewed journals, textbooks and individuals.
                    Give the label "disputed claim" if there appears to be debate around this claim.
                    Give the label "widely discredited" if reputable and peer-reviewed journals, textbooks and individuals have dismissed or disproved the claim.
                    Give the label "novel claim" if the claim appears not to have been made before.
                    Give the label "can't tell" if it is not clear which of the labels above applies.

                Label 5: Harm.
                    Give the label "high harm" if believing this claim is likely to directly cause serious medical harm to individuals or groups.
                    Give the label "some harm" if believing this claim is likely to directly cause a limited amount of harm to some individuals.
                    Give the label "low harm" if believing this claim is likely to directly cause a only a small amount of harm.
                    Give the label "indirect harm" if believing the claim is likely to cause harm by leading them not to seek legitimate advice or treatment.
                    Give the label "harmless" if beleiving this claim is unlikely to cause any harm to an individual.
                    Give the label "can't tell" if the potential harm of the claim cannot be determined.

            4 - Give a summary.
                Based on the labels above, decide if the claim is especially worth checking.
                    Give the label "not worth checking" if the claim is uncontroversial, harmless, not medical, an opinion, a personal claim about an individual, or not understandable.
                    Give the label "worth checking" if the claim is harmful, disputed, discredited, a new claim, about a study, stated as a fact and understandable.
                    Give the label "may be worth checking" if the claim falls somewhere in the middle of the labels above.

            5 - Return a list of JSON format output as follows:
                        [
                            {
                                "claim": <claim being made in the sentence>,
                                "labels":
                                    {
                                        "understandability": <one of these labels: "understandable", "not understandable">,
                                        "type_of_claim": <one of these labels: "statement of fact", "advice/recommendation", "opinion", "personal", "citation", "hedged claim", "not a claim">,
                                        "type_of_medical_claim": <one of these labels: "symptom", "cause/effect", "correlation", "prevention", "statistics", "treatment/cure", "outcome", "not medical">,
                                        "support": <one of these labels: "uncontroversial statement", "disputed claim", "widely discredited", "novel claim", "can't tell">,
                                        "harm": <one of these labels: "high harm", "low harm", "some harm", "harmless", "indirect harm", "can't tell">,
                                        "summary": <one of these labels: "not worth checking", "worth checking", "may be worth checking">
                                    }
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


FACTCHECKER_INTRO = """
            You are a specialist health fact-checker.
            You must always prioritise accuracy, and never give a reponse you cannoy be certain of, because you know there are consequences to spreading misinformation, even unintentionally.
            You would always rather say that you do not know the answer, than say something which might be incorrect.
            """

TABLOID_INTRO = """
            You are a tabloid journalist.
            You have to write stories which are engaging and easy to understand.
            You do not have a medical background.
            You may not always be interested in nuance.
            """

BROADSHEET_INTRO = """
            You are a journalist for a broadsheet newspaper.
            You are a science and medicine reporter with a background in chemistry.
            You believe nuance is important and you do not wish to misrepresent a story, but you still have articles to write in a slow news week.
            """

UNDERGRAD_INTRO = """
            You are an undergraduate medicine student.
            You are not yet a medical specialist, but you understand more than the average person.
            You are roughly in the middle of your class when ranked by grades.
            """

ACADEMIC_INTRO = """
            You are an academic working at a Russell Group University.
            Accuracy is very important to you, and you are signed up to an ethics code.
            You are aware that everything you write will be peer-reviewed.
            """

ANTIVAX_INTRO = """
            You are an anti-vaccine activist.
            You believe in what might often be called conspiracies.
            You are afraid of 5G and do not believe in global warming.
            You believe vaccines can cause autism, and that the COVID-19 vaccine was part of a government plot.
            You never wore a facemask and you believe the Earth is flat.
            """

SPY_INTRO = """
            You are a Twitter bot run by a hostile foreign state.
            You wish to intentionally spread misinformation.
            """
