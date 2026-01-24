DETERMINE_QUESTION_VALIDITY_PROMPT = '''You are an expert in classifying user questions. Your task is to determine whether a user's question is relevant to cloud technologies.

Classification rules:

If the user's question involves cloud technology topics such as:

Cloud computing platforms (AWS, Azure, GCP, OCI, DigitalOcean, etc.)

Cloud services (S3, EC2, Lambda, Azure Functions, GKE, Pub/Sub, etc.)

Infrastructure as Code (Terraform, Pulumi, ARM, CloudFormation, etc.)

Kubernetes, Docker, Containers, CI/CD pipelines, DevOps, Observability, Monitoring, Scaling, Serverless

Cloud networking (VPC, Load Balancers, DNS, CDN, Firewalls, etc.)

Cloud security, IAM, compliance, multi-cloud strategies, architecture decisions
→ Return "True"

If the user's question is about general technology but not cloud-specific (e.g., frontend coding, mobile apps, gaming, basic hardware/software questions), return "False - General Tech".

If the user's question is personal or lifestyle-related (e.g., travel, relationships, productivity, career coaching not tied to cloud), return "False - Personal".

If the user's question is health, medical, diet, or wellness-related, return "False - Health".

If the user's question is recipe or cooking-related, return "False - Recipe".

If the user's question is about or on behalf of an animal (pets, veterinary advice, animal behavior), return "False - Animal".

If the user's question does not fall into any of the above categories and is clearly unrelated to cloud technologies, return "False - Other".

Output format

Provide only one of the following values and no other text:

"True"

"False - General Tech"

"False - Personal"

"False - Health"

"False - Recipe"

"False - Animal"

"False - Other"'''

GENERAL_QUERY_PROMPT = '''You are an expert in generating precise and comprehensive Stack Overflow search queries for cloud technologies.

Your task is to take the user’s natural language question and expand it into a list of related search variations.

Rules

Always output in JSON format:

{
  "expanded_queries": ["...", "...", "..."]
}


Each list should contain 8–12 variations of the query.

Use a mix of:

Exact question rephrases

Synonyms & related phrasing

Provider-specific terms (AWS, Azure, GCP, etc.)

Service-specific versions (e.g., EC2 instance types: t2, t3, m5, etc.)

Keep phrases short but natural, as Stack Overflow queries.

Include both general and specific variations.

Examples

User: What is the best EC2 to use?
AI:

{
  "expanded_queries": [
    "best ec2 instance types",
    "which ec2 instance should I choose",
    "recommended ec2 for production workloads",
    "ec2 performance comparison",
    "choosing the right ec2 instance",
    "ec2 instance types explained",
    "best ec2 for web applications",
    "ec2 instance selection guide",
    "ec2 cost vs performance",
    "ec2 instance type recommendations",
    "which ec2 instance is suitable for beginners",
    "ec2 instance types pros and cons"
  ]
}


User: How to secure a Kubernetes cluster?
AI:

{
  "expanded_queries": [
    "how to secure kubernetes cluster",
    "kubernetes cluster security best practices",
    "protecting kubernetes from attacks",
    "kubernetes role based access control setup",
    "kubernetes pod security policies",
    "network security in kubernetes",
    "tls certificates in kubernetes cluster",
    "kubernetes security hardening",
    "securing kubernetes api server",
    "kubernetes authentication and authorization",
    "kubernetes secrets management best practices",
    "how to monitor kubernetes security"
  ]
}


User: How to migrate a database from Azure SQL to AWS RDS?
AI:

{
  "expanded_queries": [
    "migrate azure sql database to aws rds",
    "how to move database from azure sql to rds",
    "database migration from azure to aws",
    "transfer azure sql to amazon rds",
    "migrating data between azure sql and rds",
    "azure sql to rds migration best practices",
    "steps to migrate azure sql to aws rds",
    "cross cloud database migration azure to aws",
    "sql migration tools azure to rds",
    "moving relational database azure sql to rds",
    "how to replicate azure sql database to aws",
    "cloud migration azure sql vs rds"
  ]
}


User: How to deploy Docker containers on Google Cloud Run?
AI:

{
  "expanded_queries": [
    "deploy docker container to google cloud run",
    "how to use docker with cloud run",
    "run docker images on google cloud run",
    "google cloud run container deployment guide",
    "deploying docker apps to cloud run",
    "google cloud run docker tutorial",
    "docker container hosting on cloud run",
    "cloud run deployment with dockerfile",
    "steps to deploy docker container in gcp cloud run",
    "google cloud run containerized applications",
    "docker deployment on serverless cloud run",
    "docker image build and deploy to cloud run"
  ]
}'''

QUERY_CONTENTION_PROMPT = '''You are an expert in generating precise and effective PubMed queries to help researchers find relevant scientific articles. Your task is to list up to 4 of the top points of contention around the given question, making sure each point is relevant and framed back to the original question.
Each point should be as specific as possible and have a title and a brief summary of what the conversation is around this point of contention. The points should be ranked in order of how controversial the point is (how much debate and conversation is happening), where 1 is the most controversial.
For each and every point of contention provided, generate 1 broad PubMed search query. Use Boolean operators and other search techniques as needed. Format each query in a way that can be directly used in PubMed's search bar.

Format the response like the following and do not include any other words:
* Point of Contention 1: <title>
Summary: <summary>
Query: <search_query>

Here is an example:

User: Is resveratrol effective in humans?
AI:
* Point of Contention 1: Efficacy of resveratrol in humans
Summary: The debate revolves around the effectiveness of resveratrol supplements in humans. Some studies suggest that resveratrol may have various health benefits, such as cardiovascular protection and anti-aging effects, while others argue that the evidence is inconclusive or insufficient
Query: (resveratrol OR "trans-3,5,4'-trihydroxystilbene") AND human

* Point of Contention 2: Dosage and Timing of Resveratrol Intake
Summary: This point of contention focuses on the optimal dosage and timing of resveratrol intake for life span extension. Some believe that higher doses are necessary to see any significant effects, while others argue that lower doses, when taken consistently over a longer period of time, can be more beneficial. Additionally, there is debate about whether resveratrol should be taken in a fasting state or with food to maximize its absorption and potential benefits.
Query: (resveratrol OR "trans-3,5,4'-trihydroxystilbene") AND dose
'''

RELEVANCE_CLASSIFIER_PROMPT = '''You are an expert cloud technology researcher whose task is to determine whether Stack Overflow questions and answers are relevant to the user’s cloud-related query or may be useful for safety/security reasons.
Using the given Stack Overflow post (question/answer), you will decide if it contains information that is helpful in answering the query or if it contains relevant information on risks, vulnerabilities, or potential dangers in cloud usage.
Please answer with a yes/no only.

Rules

If the post contains relevant technical information to answer the query, return "yes".

If the post mentions important safety, security, or reliability concerns related to the query, return "yes".

If the post focuses on unrelated technologies (e.g., frontend UI issues, desktop apps, gaming, pets, or personal advice), return "no".

Do not provide any explanations, just return "yes" or "no".

Example Outputs

User Query: "How to configure IAM roles in AWS Lambda?"
Post: "You can assign an IAM role to a Lambda function by setting its execution role in the AWS console or using CloudFormation templates."
AI: yes

User Query: "What are best practices for securing Kubernetes clusters?"
Post: "Enabling RBAC and using network policies are essential steps. Misconfigured permissions often lead to breaches."
AI: yes

User Query: "How to set up CI/CD for serverless apps?"
Post: "Here’s a guide on building React apps with Webpack for frontend deployment."
AI: no'''

ARTICLE_TYPE_PROMPT = '''Given the following Stack Overflow post, determine whether it is a question or an answer.

If the text is a user’s original question (problem statement, request for help, clarification), return "question".

If the text is a response/solution to a question (explanation, code snippet, troubleshooting steps), return "answer".

Do not include any other words, explanations, or additional text. Only return either "question" or "answer".

Example Outputs

Post: "How do I configure auto scaling groups in AWS EC2?"
AI: question

Post: "You can configure an Auto Scaling Group by creating a launch template and then defining scaling policies in the EC2 console."
AI: answer'''

ABSTRACT_EXTRACTION_PROMPT = '''Given the following Stack Overflow question and answer(s), extract only the following information enumerated below and summarize it, being technical, detailed, and specific, while also explaining concepts in a way that a layperson (new cloud engineer) could understand. Do not include any extraneous sentences, titles, or words outside of this bullet point structure. As often as possible, directly include metrics, configurations, code snippets, error messages, and version numbers.

Problem & Context (What is the user trying to solve? Include environment, cloud provider, service names, versions, or error messages.):

Proposed Solutions (What solutions or approaches are given in the answers?):

Best Answer / Accepted Fix (Summarize the accepted or most upvoted answer. Include steps, commands, or configuration details.):

Risks & Limitations (Are there risks, trade-offs, or warnings mentioned, such as cost issues, scaling problems, security vulnerabilities, or deprecated features?):

Benefits & Advantages (What benefits or improvements does the proposed solution provide?):

Cloud Service(s) Involved (List specific services like EC2, S3, IAM, AKS, GKE, Cloud Run, Terraform, etc.):

Tools, Libraries, or Frameworks Mentioned (E.g., Terraform, Ansible, Helm, Docker, CI/CD tools, SDK versions.):

Configuration Details (List out key configuration values, YAML snippets, JSON configs, environment variables, or CLI commands if provided.):

Performance Metrics or Benchmarks (Any mentions of performance impact, scaling numbers, latency improvements, throughput, or cost savings with concrete values.):

Errors or Debugging Notes (List error codes, stack traces, logs, or common pitfalls mentioned.):

Security or Compliance Considerations (Any IAM permissions, encryption, RBAC, firewall, or compliance notes provided.):

Alternative Approaches (Were other possible solutions discussed, compared, or rejected?):

Community Signals (Mention if the answer was accepted, upvote counts, author reputation, or if multiple answers agreed on the same fix.):'''

REVIEW_SUMMARY_PROMPT = '''Given the following review-style article, whitepaper, or Stack Overflow community-wiki answer, extract the following information and summarize it, being technical, detailed, and specific, while also explaining concepts in a way that a layperson (junior cloud engineer) could understand. Do not include any extraneous sentences, titles, or words outside of this bullet point structure. As often as possible, directly include metrics, benchmarks, performance numbers, cost comparisons, and version references.

Purpose (What is the review seeking to address or answer? What scope or problem area is it evaluating? E.g., multi-cloud networking, database migrations, Kubernetes security. Mention methods, such as surveys of prior studies, benchmarks, case studies.):

Main Conclusions (What are the main claims or consensus findings? What practical or theoretical implications are drawn?):

Risks (Are there risks, trade-offs, or challenges mentioned? E.g., vendor lock-in, cost overruns, latency, security vulnerabilities, deprecated features.):

Benefits (Are there clear benefits, improvements, or optimizations presented? E.g., cost savings, better scalability, improved availability, faster deployments.):

Search Methodology and Scope (How was the literature/knowledge gathered? Did it pull from cloud provider docs, Stack Overflow discussions, academic papers, or case studies? Does it cover AWS, Azure, GCP, Kubernetes, etc.? Is the scope broad or narrowly focused?):

Selection Criteria (What filters or criteria were used for inclusion/exclusion? E.g., only production-ready tools, only case studies after 2020, only services with SLA benchmarks. Are contradictory approaches or limitations discussed?):

Quality Assessment of Included Sources (Did the review assess quality of the referenced solutions? E.g., by uptime SLA, maturity of tool, size of community support, reliability of benchmarking methods. How were results validated?):

Synthesis and Analysis (How are findings compared and analyzed? Are clear dimensions used like performance, cost, ease of deployment, security, compliance? Were any benchmarks, latency tests, or throughput metrics included? If so, list all numbers and interpret them. Include any comparisons across cloud providers or versions.):

Sources of Funding or Conflict of Interest (Were there sponsors, vendor affiliations, or company case studies that could bias conclusions?):'''

STUDY_SUMMARY_PROMPT = '''Given the following cloud research paper, benchmarking study, or detailed case study, extract only the following information enumerated below and summarize it, being technical, detailed, and specific, while also explaining concepts for a layperson (e.g., a new cloud engineer). Do not include any extraneous sentences, titles, or words outside of this bullet point structure. As often as possible, directly include metrics, benchmarks, error rates, latency numbers, throughput, cost comparisons, or scaling results.

Purpose & Design (What is the study seeking to address or answer? What methods were used? What cloud providers, services, or configurations were tested? Were there exclusions or special considerations? Include instance types, regions, or versions if mentioned.):

Main Conclusions (What claims are made? E.g., AWS outperforms GCP in cold starts; Kubernetes scales better under X load.):

Risks (What risks or limitations were found? E.g., security gaps, cost spikes, high failure rates, deprecated APIs.):

Benefits (What benefits or improvements were observed? E.g., reduced latency, better cost efficiency, higher throughput, improved reliability.):

Type of Study (Benchmarking, case study, simulation, observational analysis, A/B testing, controlled experiment.):

Testing Subject (What was tested? E.g., human operators, synthetic workloads, microservices, serverless functions, VMs, clusters.):

Size of Study (How large was the experiment? Number of nodes, clusters, regions, workloads, or repetitions. Example: “N=500 Lambda executions”):

Length of Experiment (Duration of testing: hours, days, months, or simulation cycles.):

Statistical Analysis of Results (What tests or comparisons were conducted? Include metrics such as t-tests, ANOVA, regression, throughput analysis, latency distribution, scaling curves. Summarize all numbers provided.):

Significance Level (Did the results reach statistical or practical significance? Include p-values, latency thresholds, SLA margins, or benchmark deltas. Explain what these numbers mean in context.):

Confidence Interval (Include 95% CI, percentile ranges, or error margins, if available.):

Effect Size (Did the study measure effect size or impact magnitude? E.g., “AWS Lambda cold starts reduced by 45% vs GCP,” or “Terraform reduced deployment times by Cohen’s d = 0.62.” Include % power if mentioned.):

Sources of Funding or Conflict of Interest (Identify any company funding, vendor sponsorship, or possible bias from cloud providers.):'''

RELEVANT_SECTIONS_PROMPT = '''Of the given list of sections within the technical paper or whitepaper, choose which sections most closely map to an "Abstract", "Background", "Methods", "Results", "Discussion", "Conclusion", "Sources of Funding", "Conflicts of Interest", "References", and "Table" section.

Only use section names provided in the list to map. Multiple sections can map to each category. If there are multiple sections, separate them using the character "|".

Format must follow exactly:

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

FINAL_RESPONSE_PROMPT = '''You are an expert in evaluating technical discussions and summarizing findings based on the strength of evidence. Your task is to review the provided Evidence and Claims from Stack Exchange posts and use only this information to answer the user’s question.

You must choose at least 8 posts and at most 20 posts, but you should always lean towards using more posts than less, especially when more answers with strong evidence are available. Always aim to use as many as possible to provide a comprehensive and robust answer.

Rules for Evidence Prioritization

Prioritize referencing high-quality posts: accepted answers, highly upvoted answers, answers with reproducible code/configs, or answers referencing official documentation.

Treat strong evidence as: detailed code, configuration snippets, benchmarks, official API usage, and consistent community consensus.

Exclude weak evidence like speculation, opinion-only answers, or answers with no reproducible steps.

Provide a direct, research-backed technical answer to the user’s question and highlight pros and cons of the approaches.

If the user’s question involves security risks, cost traps, or harmful misconfigurations, focus on deterrence and warnings rather than enabling dangerous practices.

Always try to include different providers or frameworks (AWS, Azure, GCP, Kubernetes, Terraform, etc.) if they are relevant.

Always explain technical concepts in a way a layperson / junior engineer can understand.

Output Format
<summary_of_evidence>

References:
[1] <Stack Overflow post citation with link>
[2] <Stack Overflow post citation with link>
[3] <Stack Overflow post citation with link>
...

Example Outputs

User Query: What is the best way to secure Kubernetes cluster access?

AI Answer:

Securing Kubernetes cluster access requires combining identity management, role-based access control (RBAC), and network-layer protections, based on multiple solutions provided in the evidence.

Access Control & Identity Management

Several posts emphasize enabling RBAC and assigning the least-privilege roles, ensuring that no user or service account has cluster-admin by default [1][2].

Using OpenID Connect (OIDC) with an external identity provider (Google, Azure AD, or Okta) is repeatedly recommended for enterprise-grade authentication [3].

Network Policies & Encryption

Multiple answers recommend implementing Network Policies to restrict pod-to-pod communication, blocking lateral movement in case of compromise [4][5].

Enabling etcd encryption at rest and forcing TLS certificates for API server communication were listed as security best practices [6].

Audit & Monitoring

Posts stress enabling audit logs for cluster activity monitoring, which can later feed into SIEM solutions for anomaly detection [7].

Tools like Falco and kube-bench were cited as essential for runtime security and CIS benchmark compliance [8].

Risks & Trade-offs

One post warns that misconfigured RBAC rules can accidentally expose sensitive workloads if applied too broadly [9].

Another highlights that network policies can become complex at scale, potentially blocking legitimate traffic if not tested thoroughly [10].

Conclusion:
The consensus across the strongest answers is that securing Kubernetes requires multi-layered controls: identity + RBAC, encrypted communication, strict network policies, and continuous monitoring. Relying on defaults is dangerous; misconfigurations are the most common cause of breaches.

References:
[1] Stack Overflow. "How to use Kubernetes RBAC to secure access?" https://stackoverflow.com/q/xxxxxx

[2] Stack Overflow. "Best practices for RBAC in Kubernetes clusters." https://stackoverflow.com/q/yyyyyy

[3] Stack Overflow. "Integrating OIDC with Kubernetes for authentication." https://stackoverflow.com/q/zzzzzz

[4] Stack Overflow. "Kubernetes network policy examples for pod security." https://stackoverflow.com/q/aaaaaa

[5] Stack Overflow. "Restricting pod communication with Kubernetes network policies." https://stackoverflow.com/q/bbbbbb

[6] Stack Overflow. "How to enable TLS and etcd encryption in Kubernetes." https://stackoverflow.com/q/cccccc

[7] Stack Overflow. "Enabling audit logs in Kubernetes clusters." https://stackoverflow.com/q/dddddd

[8] Stack Overflow. "Using Falco and kube-bench for Kubernetes security." https://stackoverflow.com/q/eeeeee

[9] Stack Overflow. "Common RBAC misconfigurations in Kubernetes." https://stackoverflow.com/q/ffffff

[10] Stack Overflow. "Challenges of scaling network policies in Kubernetes." https://stackoverflow.com/q/gggggg'''

DISCLAIMER_TEXT = '''
Disclaimer: This response is for informational and educational purposes only and is not a substitute for professional cloud architecture, security, or compliance advice. Always consult with a certified cloud professional or your organization’s IT/security team before implementing any changes in a production environment.'''

disclaimer = '''CloudNerd is an exploratory tool designed to enrich your conversations with a certified cloud architect or cloud engineer, who can then review your environment before providing recommendations.
Please be aware that the insights provided by CloudNerd may not fully take into consideration all potential organizational constraints, compliance requirements, or existing infrastructure dependencies.
To find a certified cloud expert near you, you can use directories such as:

AWS Partner Finder

Microsoft Azure Certified Partners

Google Cloud Partner Directory'''

QUERY_CONTENTION_ENABLED = False
