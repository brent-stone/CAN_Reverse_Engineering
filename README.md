# Automated CAN Payload Reverse Engineering

## NOTICE
> The views expressed in this document and code are those of the author and do not reflect the official policy or position of the United States Air Force, the United States Army, the United States Department of Defense or the United States Government. This material is declared a work of the U.S. Government and is not subject to copyright protection in the United States. Approval for public disclosure of this code was approved by the 88th Air Base Wing Public Affairs on 08 March 2019 under case number 88ABW-2019-0910. Unclassified disclosure of the dissertation was approved on 03 January 2019 under case number 88ABW-2019-0024.
-----------------------------------------------------------------------------------------

This project houses Python and R scripts intended to facilitate the automated reverse engineering of Controller Area Network (CAN) payloads observed from passenger vehicles. This code was originally developed by Dr. Brent Stone at the Air Force Institute of Technology in pursuit of a Doctor of Philosophy in Computer Science. Please see the included dissertation titled "Enabling Auditing and Intrusion Detection for Proprietary Controller Area Networks" for details about the methods used. Please open an issue letting me know if you find any typos, bad grammar, your copyrighted images you want removed, or other issues!

Special thank you to Dave Blundell, co-author of the Car Hacker's Handbook, and the Open Garages community for technical advice and serving as a sounding board.

## Tips and Advice
These scripts won't run immediately when cloning this repo. Hopefully these tips will save you time and frustration saying "WHY WONT THESE THINGS WORK!?!?!" Please ask questions by posting in the [Open Garages Google group](https://groups.google.com/forum/#!forum/open-garages). These scripts were developed and tested using Python 3.6. Please make sure you have the Numpy, Pandas, & scikit-learn packages available to your Python Interpreter.


The files are organized with an example CAN data sample and three folders. Each folder is a self-contained set of interdependent Python classes or R scripts for examining CAN data in the format shown in the example loggerProgram0.log. Different file formats can be used by adjusting PreProcessor.py accordingly.

* Folder 1: **Pipeline**
  * Simply copy loggerProgram0.log into this folder and run main.py.
  * This is the most basic implementation of the pipeline described in the dissertation. Over 80% of the code is referenced from main.py. Follow the calls made in main.py to see how the data are sequentially processed and saved to disk.
  * The remaining 20% is unused portions of code which were left in place to either serve as a reference for different ways of doing things in Python or interesting experiments which were worth preserving (like the Smith-Waterman search).

* Folder 2: **Pipeline_multi-file**
  * This is the most complete and robust implementation of the concepts presented in the dissertation; however, the code is also more complicated to enable automated processing of many CAN data samples at one time. If you aren't already very comfortable with Python and Pandas, make sure you understand how the scripts in the **Pipeline** folder work before attempting to go through this expanded version of the code.

  * This folder includes the same classes from **Pipeline**. However, **SOME BUGS WERE FIXED HERE** but **NOT** in the classes saved in **Pipeline**. If a generous soul wants to transplant the fixes back into **Pipeline**, I will happily merge the fork.

  * Make sure you read the comments about the expected folder structure!

* Folder 3: **R Scripts**
  * The R scripts require the [rEDM](https://CRAN.R-project.org/package=rEDM) package. Look for commands_list.txt for a sequential series of R commands. For more information about EDM, see U.C. San Diego's Sugihara Lab homepage: https://deepeco.ucsd.edu/.

  * The folders "city" and "home" include .csv files of engine RPM, brake pressure, and vehicle speed time series during different driving conditions. Each folder includes a "commands_list_####.txt" file for copy-paste R commands to analyze this data using the rEDM package.

  * .Rda files and .pdf graphical output are examples of output using the R commands and provided .csv data.
 

[APRIL 2020 UPDATE]
Will Freeman added support for command line arguments and can-utils log format pre-processing.
Usage is:

Example use with can-utils log format
python Main.py -c inputFile.log

python Main.py --can-utils inputFile.log

Example use with original format
python Main.py originalFormat.log

Example use with ./loggerProgram0.log
python Main.py
  
## Script specific information by folder
### Pipeline
**Input**: CAN data in the format demonstrated in loggerProgram0.log
* **Main.py**
  1. **Purpose**: This script links and calls all remaining scripts in this folder. It handles some ‘global’ variables used for modifying the flow of data between scripts as well as any files output to the local hard disk.
* **PreProcessor.py**
  1. **Purpose**: This script is responsible for reading in .log files and converting them to a runtime data structure known as a Pandas Data Frame. Some ‘data cleaning’ is also performed by this script. The output is a dictionary data structure containing ArbID runtime objects based on the class defined in **ArbID.py**. **J1979.py** is called to attempt to identify and extract data in the Data Frame related to the SAE J1979 standard. J1979 is a public communications standard so this data does not need to be specially analyzed by the following scripts.
* **LexicalAnalysis.py**
  1. **Purpose**: This script is responsible for making an educated guess about the time series data present in the Data Frame and ArbID dictionary created by **PreProcessor.py**. Individual time series are recorded using a dictionary of Signal runtime objects based on the class defined in **Signal.py**.
* **SemanticAnalysis.py**
  1. **Purpose**: This script generates a correlation matrix of Signal time series produced by **LexicalAnalysis.py**. That correlation matrix is then used to cluster Signal time series using an open source implementation of a Hierarchical Clustering algorithm.
* **Plotter.py**
  1. **Purpose**: This script uses an open source plotting library to produce visualizations of the groups of Signal time series and J1979 time series produced by the previous scripts.

**Output**: This series of scripts produces an array of output depending on the global variables defined in **Main.py**. This output may include the following:
*	‘Pickle’ files of the runtime dictionary and Data Frame objects using the open source Pickle library for Python. These files simply speed up repeated execution of the Python scripts when the same .log file is used for input to **Main.py**.
* Comma separated value (.csv) plain text files of the correlation matrix between time series data present in the .log file.
* Graphics of scatter-plots of the time series present in the .log file.
* A graphic of the dendrogram produced during Hierarchical Clustering in **SemanticAnalysis.py**. A dendrogram is a well-documented method for visualizing the results of Hierarchical Clustering algorithms.


### Pipeline_multi-file
**Input**: CAN data in the format demonstrated in loggerProgram0.log. 
* **Main.py** and the other identically named scripts from **Pipeline** have been updated to allow the scripts to automatically import and process multiple .log files.
* **FileBoi.py**
  1. **Purpose**: This is a series of functions which handle the logistics of searching for and reading in data from multiple .log files.
* **Sample.py**
  1. **Purpose**: Much of the functionality present in **Main.py** in **Pipeline** has been moved into this script. This works in conjunction with **FileBoi.py** to handle the logistics of working with multiple .log files.
* **SampleStats.py**
  1. **Purpose**: This script produces and records a series of basic statistics about a particular .log file.
* **Validator.py**
  1. **Purpose**: This script performs a common machine learning validation technique called a ‘train-test split’ to quantify the consistency of the output of **LexicalAnalysis.py** and **SemanticAnalysis.py**. This was used in conjunction with **SampleStats.py** to produce quantifiable findings for research papers and the dissertation.
**Output**: The output of **Pipeline_multi-file** is the same as **Pipeline** but organized according to the file structure used to store the set of .log files used as input. **SampleStats.py** and **Validator.py** also produce some additional statistical metrics regarding each .log file.

### R
**Input**: Plain-text .csv files containing time series data such as those included in this folder. 
* **commands_list.txt, commands_list_city.txt, commands_list_home.txt**
  1. **Purpose**: This is a list of R commands for the publically available rEDM package. The intent is to perform analysis of the time series according to the rEDM user guide. Each version is highly similar and customized only to point to a different .csv file for input and .pdf file to visualize the output.


**Output**:
* .Rda files
  1. **Purpose**: These are machine readable files for storing R Data Frame objects to disk. All of these files were generated using the operations listed in commands_list.txt, commands_list_city.txt, commands_list_home.txt, and the provided .csv files.
* .pdf files
  1. **Purpose**: These are visualizations of the output of the R commands using the provided .csv files.
