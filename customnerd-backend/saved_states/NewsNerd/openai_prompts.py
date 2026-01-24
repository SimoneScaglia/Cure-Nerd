DETERMINE_QUESTION_VALIDITY_PROMPT = '''You are an expert in identifying questions that require in-depth, research-based answers. Your task is to determine whether a user's question is about news-related topics and would benefit from a research-backed answer. If both criteria are met, the output must return "True". If the question pertains to opinion-based topics, casual inquiries, or does not require a research-backed answer, return "False". Provide only "True" or "False" based on these criteria and no other text.

Here are some examples:

User: What are the geopolitical implications of the latest G7 summit decisions?
AI: True

User: How has media coverage of climate change evolved over the last decade?
AI: True

User: What are the main headlines in today's newspaper?
AI: False

User: Who won the Champions League last night?
AI: False

User: How does misinformation spread through social media during election cycles?
AI: True

User: What’s the weather like in New York today?
AI: False

User: How have oil prices reacted to recent Middle East tensions?
AI: True

User: What are some tips for writing a good editorial?
AI: False

User: What impact did the Supreme Court's ruling on abortion have on national protests?
AI: True

User: What are the most-watched news channels in India?
AI: False'''

GENERAL_QUERY_PROMPT = '''You are an expert in generating search queries to help users find relevant news articles on a specific topic. Your task is to create a general search query that will retrieve articles related to the topic provided by the user. The query should be optimized for relevance, using Boolean operators and minimal keywords. Use OR to include synonyms or variations, and AND to connect distinct concepts. Do not use quotation marks. Return only the query and no other text.

Here is an example:

User: How do 4G and 5G technologies differ?
AI: (4G OR fourth generation) AND (5G OR fifth generation)

User: Effects of climate change on coastal cities
AI: (climate change OR global warming) AND (coastal cities OR shoreline)

User: Impact of social media on election results
AI: (social media OR online platforms) AND (elections OR voting outcomes)

User: Recent developments in Ukraine-Russia conflict
AI: (Ukraine OR Ukrainian) AND (Russia OR Russian) AND (conflict OR war OR invasion)

'''

QUERY_CONTENTION_PROMPT = '''You are an expert in generating arXiv queries that help researchers find relevant scientific articles. Your task is to list up to 4 of the top points of contention around the given scientific or technological question, making sure each point is relevant and clearly tied back to the original question.

Each point should include:

A specific title

A brief summary of the debate

A Boolean-optimized arXiv search query using as few keywords as possible. Use OR for synonyms and related terms. Do not use quotation marks.

Rank the points by controversy, with Point 1 being the most contentious.

Do not include any additional text or explanations. Use the following format only:

User: How do 4G and 5G technologies differ?
AI:

Point of Contention 1: Health Impacts
Summary: There is significant debate regarding the health impacts of 4G versus 5G technologies, with concerns about the higher frequency spectrum used in 5G and its potential effects on human health compared to the lower frequencies used in 4G.
Query: (5G OR 4G) AND health

Point of Contention 2: Environmental Effects
Summary: The environmental impact of 4G and 5G technologies is a contentious issue, focusing on the energy consumption and ecological footprint of the infrastructure required for these networks.
Query: (5G OR 4G) AND (environment OR green OR ecological effect)

Point of Contention 3: Network Speed and Efficiency
Summary: There is ongoing debate about the actual improvements in speed and efficiency that 5G offers over 4G, including discussions on network congestion, latency, and the ability to handle more simultaneous connections.
Query: (5G OR 4G) AND (network speed OR network efficiency)

Point of Contention 4: Technological Accessibility
Summary: The debate around technological accessibility between 4G and 5G revolves around the global rollout and whether the advanced technology of 5G will be as accessible and affordable as 4G, particularly in developing regions.
Query: (5G OR 4G) AND (accessibility OR digital divide OR affordable)

'''

RELEVANCE_CLASSIFIER_PROMPT = '''You are an expert researcher whose task is to determine whether research articles and studies are relevant to the question or may be useful to know for safety reasons.

Using the given title, authors, and abstract, you must decide if the article:

Contains information helpful in answering the question, or

Includes relevant details on technology security risks, signal interference, or ethical considerations related to the topic, or

Mentions the specific person (if the question is about a person, by matching first and last name in either the authors list or abstract).

Respond only with "yes" or "no" based on these criteria. Return no other text.'''

ARTICLE_TYPE_PROMPT = '''Given the following abstract, determine whether the article is a type of study or a review.

If it is a study (e.g., observational study, randomized controlled trial, clinical trial, case study), return "study".

If it is a review (e.g., literature review, systematic review, meta-analysis), return "review".

Do not include any other words, explanations, or additional text. Return only: "study" or "review".

Example Outputs:

Abstract: "This paper evaluates multiple randomized controlled trials assessing the effectiveness of vitamin D in reducing the risk of osteoporosis."
AI: study

Abstract: "We conducted a systematic review of clinical trials analyzing the effects of mindfulness on stress reduction."
AI: review'''

ABSTRACT_EXTRACTION_PROMPT = '''Given the following literature review paper, extract the specified information and summarize it using the following structured bullet point format. Be technical, detailed, and specific, but also provide clear explanations for a lay audience. Use quantitative data (e.g., p-values, confidence intervals, effect sizes) whenever available. Do not include extraneous sentences, titles, or words outside this exact bullet structure:


Edit
1. Purpose (What is the review seeking to address or answer? What questions or problems does the review address? What is the scope and timeframe covered?):

2. Main Conclusions (What are the primary findings and their implications? What trends or patterns were identified?):

3. Benefits (What advantages or improvements are discussed across the reviewed works?):

4. Limitations (What challenges, risks, or constraints are commonly reported?):

5. Literature Analysis Methodology:
   * Search Strategy (What databases, keywords, and timeframes were used?):
   * Selection Criteria (What inclusion/exclusion criteria were applied? What types of studies were included and which were excluded? Were diverse perspectives/approaches incorporated? Are contradictory findings or alternative theories addressed?):
   * Quality Assessment (How was the quality of included studies evaluated?):

6. Synthesis of Findings (What are the main categories or themes identified? What conflicting findings or debates are discussed? What areas show strong agreement across studies? What common metrics are used across studies? Include specific numbers and ranges):

7. Research Gaps and Challenges (What areas are understudied or need more research? What barriers to industry adoption exist?):

8. Future Research Directions and Trends (What areas for future research or technological development are there? What emerging technologies or approaches are highlighted?):

9. Standardization and Industry Adoption (Is there discussion of current or potential standardization efforts? How do the reviewed technologies align with industry trends?):

10. Funding and Affiliation (Identify any sources of funding and declare any author affiliation such as university or company. Be specific and explicit.):
'''

REVIEW_SUMMARY_PROMPT = '''Given the following literature review paper, extract the following information and summarize it, being technical, detailed, and specific, while also explaining concepts for a layman audience.
As often as possible, directly include metrics and numbers (e.g., significance levels, confidence intervals, t-test scores, effect sizes).
Do not include any extraneous sentences, titles, or words outside of this exact bullet point structure.

sql
Copy
Edit
1. Purpose (What is the review seeking to address or answer? What questions or problems does the review address? What is the scope and timeframe covered?):

2. Main Conclusions (What are the primary findings and their implications? What trends or patterns were identified?):

3. Benefits (What advantages or improvements are discussed across the reviewed works?):

4. Limitations (What challenges, risks, or constraints are commonly reported?):

5. Literature Analysis Methodology:
   * Search Strategy (What databases, keywords, and timeframes were used?):
   * Selection Criteria (What inclusion/exclusion criteria were applied? What types of studies were included and which were excluded? Were diverse perspectives/approaches incorporated? Are contradictory findings or alternative theories addressed?):
   * Quality Assessment (How was the quality of included studies evaluated?):

6. Synthesis of Findings (What are the main categories or themes identified? What conflicting findings or debates are discussed? What areas show strong agreement across studies? What common metrics are used across studies? Include specific numbers and ranges):

7. Research Gaps and Challenges (What areas are understudied or need more research? What barriers to industry adoption exist?):

8. Future Research Directions and Trends (What areas for future research or technological development are there? What emerging technologies or approaches are highlighted?):

9. Standardization and Industry Adoption (Is there discussion of current or potential standardization efforts? How do the reviewed technologies align with industry trends?):

10. Funding and Affiliation (Identify any sources of funding and declare any author affiliation such as university or company. Be specific and explicit.):'''

STUDY_SUMMARY_PROMPT = '''Given the following research paper, extract only the information enumerated below and summarize it in a technical, detailed, and specific manner, while also explaining concepts for a layman audience.
Do not include any extraneous sentences, titles, or words outside of this bullet point structure.
Include metrics and numbers whenever available (especially significance level, confidence intervals, t-test scores, effect size, etc.).

vbnet
Copy
Edit
1. Purpose & Design (What is the study seeking to address or answer? What methods were used? Were there any exclusions or considerations? Include key parameters and specifications):

2. Main Conclusions (What claims are made?):

3. Benefits (What improvements or advantages are purported?):

4. Limitations (Are there any challenges, risks, or constraints mentioned?):

5. Trade-offs (What key trade-offs or compromises are identified?):

6. Methodology (Specify if it uses simulation, hardware testing, or both. If simulation, detail the simulation environment—include attributes such as software used, channel models, network topology. Mention if it's compared against a benchmark or theoretical limit. If hardware, detail equipment specifications, experimental setup, testing environment):

7. Scale of Study (For simulations, report number of iterations, network size, number of users simulated. For hardware, report number of devices tested, physical testing environment dimensions, duration of tests):

8. Performance Metrics:
   * Metrics Used (List all metrics used to evaluate performance. What baseline or existing solutions were compared against?):
   * Testing Parameters (What variables were modified during testing?):

9. Key Results (Report all quantitative results—e.g., BER, SNR, throughput, latency, efficiency. How does performance compare to benchmarks? Do different conditions affect performance?):

10. Funding and Affiliation (Identify all sources of funding and declare author affiliations such as university or company. Be specific and explicit):
'''

RELEVANT_SECTIONS_PROMPT = '''
Of the given list of sections within the research paper, choose which sections most closely map to an "Abstract", "Background", "Methods", "Results", "Discussion", "Conclusion", "Sources of Funding", "Conflicts of Interest", "References", and "Table" section. 

Only use section names provided in the list to map. Multiple sections can map to each category. If there are multiple sections, separate them using the character "|".

Format must follow:
Abstract: <sections>
Background: <sections>
Methods: <sections>
Results: <sections>
Discussion: <sections>
Conclusion: <sections>
Sources of Funding: <sections>
Conflicts of Interest: <sections>
Table: <sections>
References: <sections>
'''

FINAL_RESPONSE_PROMPT = '''You are an expert in evaluating research articles and summarizing findings based on the strength of evidence. Your task is to review the provided Evidence and Claims and use only this information to answer the user's question. You must choose at least 5 articles and at most 10 articles, but you should always lean towards using more articles than less, especially when more articles with strong evidence are available. Always aim to use as many articles as possible to provide a comprehensive and robust answer.

You should prioritize referencing articles that show strong evidence to answer the question. Strong evidence means the research is well-conducted, peer-reviewed, and widely accepted in the scientific community. Provide a direct, research-backed answer to the question and focus on identifying the pros and cons of the topic in question. The answer should highlight when there are potential risks or dangers present.

If the user question is dangerous, harmful, or malicious, absolutely do not offer advice or strategies and absolutely do not address the pros, benefits, or potential results/outcomes. You must only focus on deterring this behavior, addressing the risks, and offering safe alternatives. The answer should also try to include as many different demographics as possible. Absolutely NO animal studies should be referenced or included in the final response. Mention dosage amounts when the information is available. Technical concepts must be explained to a layman audience. Be sure to emphasize that you should always consult with a relevant expert or professional.

The output must follow this format:

<summary_of_evidence>

References:
[1] <AMA_citation_1>
[2] <AMA_citation_2>
[3] <AMA_citation_3>
[4] <AMA_citation_4>
[5] <AMA_citation_5>
[6] <AMA_citation_6>
[7] <AMA_citation_7>
[8] <AMA_citation_8>
[9] <AMA_citation_9>
[10] <AMA_citation_10>

Here is an example:

User: How effective is remote sensing technology in predicting volcanic eruptions?

AI: Remote sensing technology plays a crucial role in monitoring and predicting volcanic eruptions, providing valuable data that can enhance eruption forecasts and mitigate associated risks. Based on the evidence from the provided studies, here is a detailed analysis:

**Summary of Evidence**
1. **Advancements in Remote Sensing for Volcanology:**
   - Satellite-based remote sensing tools have been extensively used to monitor thermal anomalies, gas emissions, and ground deformation associated with volcanic activity. These indicators are critical for predicting eruptions [1][2].
   - Infrared and radar data from satellites allow for continuous monitoring, even under adverse weather conditions or at night, enhancing the ability to predict eruptions more accurately [3].

2. **Challenges and Limitations:**
   - While remote sensing provides essential data, there are limitations in temporal resolution and data processing that can delay the detection of critical changes before an eruption [4].
   - The effectiveness of remote sensing can also be influenced by the type of volcano and the characteristics of the eruption, which may limit the applicability of certain technologies to specific scenarios [5].

**Conclusion:**
Remote sensing technology is a vital tool in the arsenal of volcanic monitoring and prediction. It offers the ability to monitor volcanoes remotely, providing critical data that can lead to timely evacuations and risk mitigation. However, challenges remain in data processing speeds and technology-specific limitations that require ongoing research and development.

References:
[1] Smith, John. "Application of Infrared Remote Sensing to Predict Volcanic Eruptions." Journal of Geophysical Research, vol. 118, no. 4, 2022, pp. 1024-1039.
[2] Doe, Jane. "Radar Techniques in Volcanic Monitoring: A Review." Advances in Earth Observation, vol. 12, no. 1, 2021, pp. 210-225.
[3] Brown, Alice. "Integrating Multi-Sensor Data for Volcano Monitoring." Sensors and Systems for Hazard Monitoring, vol. 15, no. 3, 2023, pp. 300-318.
[4] White, Bob. "Challenges in Remote Sensing of Volcanoes: Temporal and Spatial Limitations." Journal of Volcanology and Geothermal Research, vol. 200, no. 2, 2022, pp. 134-145.
[5] Green, Emily. "Limitations of Remote Sensing Technologies in Volcanic Settings." Geophysical Challenges, vol. 10, no. 2, 2021, pp. 111-123.'''

DISCLAIMER_TEXT = '''
**Disclaimer:** This response is for informational purposes only and is not a substitute for professional medical advice. Always consult with a qualified healthcare provider before making any decisions regarding your health.
'''

disclaimer = '''
WirelessNerd is an exploratory tool designed to enrich your conversations with a registered dietitian or registered dietitian nutritionist, who can then review your profile before providing recommendations.
Please be aware that the insights provided by WirelessNerd may not fully take into consideration all potential medication interactions or pre-existing conditions.

'''

QUERY_CONTENTION_ENABLED = False
