# Omitted variable bias
Omitted variable bias results when effects of variables not included in a model (some of which may be unobserved) are attributed to variables included a model. Omitted variable bias can lead to overestimated or underestimated effects and invalid conclusions. This phenomenon is well understood and is commonly discussed as part of many introductory statistics and econometrics texts. In this project, we sought to bring omitted variable bias to the attention of the physics education research community through examples with our own datasets.

# Version1

See `Version1` for more information. We first approached this problem by using data collected with four standardized physics assessments administered at Cornell University over two years. We showed, using several different models with different control variables, how the estimated differences in posttest scores between different groups of students on these assessments varied from model to model.

# Current version

In our current analyses, we use only one standardized assessment, the Colorado Learning Attitudes about Science Survey for Experimental Physics (E-CLASS), and explore omitted variable bias using analytic solutions. We use three case studies of simple models of posttest scores using the E-CLASS dataset. In our first model we used only two independent variables: students' pretest score and intended major. In our second model we included the type of lab instruction students received as an additional control variable. In our third model, we used students' URM status instead of lab instruction as a control variable. Our results demonstrated that that the estimated effect of students' major on students' E-CLASS scores varies depending on which control variables are included in our model.

In the second part of our analysis, we used a hypothetical model where the outcome was determined by only three independent variables. We showed visually, using [analytic solutions](https://journals.sagepub.com/doi/abs/10.1080/07388940500339183?casa_token=z7dzzbh4uCoAAAAA:2TaEIuaIQW7RLCR1vTsK_FpI13yAUcJhLlpBP99D-kOKH39iCR4DkpA8xpiBye79Ifr0NuZGgjyVZw) for this model, how the relative bias on independent variables depended on correlations between included and omitted variables and true effect sizes of independent variables.

# Data Processing

This project involved pulling together data from four different assessments and registrar data provided by Cornell University. `Data_Processing` includes python scripts for processing and merging these data sources.
