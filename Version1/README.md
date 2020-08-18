# Omitted variable bias v1

In this analysis, conducted in `OVB_Regressions.Rmd`, we used data collected at Cornell University using four standardized physics assessments: the Conceptual Survey of Electricity and Magnetism (CSEM), the Colorado Learning Attitudes about Science Survey for Experimental Physics (E-CLASS), the Mechanics Baseline Test (MBT), and the Physics Lab Inventory of Critical thinking (PLIC). Four all four assessments, we showed how the interpretation of differences in performance between groups of students varied depending on which control variables were used in the analysis.

`PowerAnalysis.Rmd` includes a simple power analysis illustrating how the power of hypothesis tests with linear regressions vary with effect size and sample size. We used model specifications similar to those in `OVB_Regressions.Rmd` to determine what sample size would be needed to achieve the statistical power we desired in our analysis. We present an additional Monte Carlo power analysis in `OVB_Regressions.Rmd` that uses linear mixed-effects models and the effect sizes found in our real data.

