# Data processing

The python scripts here were used to pull together data from the university registrar and four standardized physics assessments: the Conceptual Survey of Electricity and Magnetism (CSEM), the Colorado Learning Attitudes about Science Survey for Experimental Physics (E-CLASS), the Mechanics Baseline Test (MBT), and the Physics Lab Inventory of Critical thinking (PLIC). Scripts `xxx_Processing.py` provide functions for filtering, processing, scoring, matching pretest and posttest data, and building master data files for each of the CSEM, E-CLASS, and MBT. The PLIC is administered internationally and functions for dealing with PLIC data are provided separately in the `PLIC` repository.

`Assessment_Registrar_Processing.py` provides functions for filtering and processing university registrar data, and functions for merging registrar data with assessment data to build one master data file with assessment scores and registrar information, which we use in our analyses.
