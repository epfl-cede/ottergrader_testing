from otter.api import grade_submission # grading api
import glob # patterns in accessing file paths
import pandas as pd # pandas for saving as csv
pd.set_option('display.max_colwidth', None)
import csv # csv quoting options
from datetime import datetime # date formatting
from IPython.display import display # display for debug
import itertools as it # iteration tools
import os # file management tools


def grade_and_writeCSV(submissionfile, graderzip, graderoutputfolder, 
                       graderdetailsfilename="graderdetails", graderresultfilename="graderresult", 
                       includetestcasemessages=False):
    """
    Grades 1 individual submission file, saves the grading results into CSV files and returns them.

    Parameters:
    - submissionfile: path to the individual file to grade (notebook)
    - graderzip: path to the zip of the grader, generated in the assign phase
    - graderoutputfolder: name of the folder where to write the CSV files with the outputs of the grading
    - graderdetailsfilename: name of the file where to write the detailed output of the grading (points per exercises and tests outcomes) - default is "graderdetails"
    - graderresultfilename: name of the file where to write the overall grade and feedback message - default is "graderresult"
    - includetestcasemessages: boolean indicating whether the detailed output from the tests should be included - default is False

    Returns: 
    - graderresultdf: Pandas dataframe with the resulting grade for this submission (3 columns: "Submission Name", "Grade", "Possible")
    - graderdetailsdf: Pandas dataframe with the detailed output of the grading (4 columns: "Exercise", "Grade", "Possible", "Feedback")
    """

    # Call the autograder and get the result
    gradingoutput = grade_submission(submissionfile, graderzip, quiet=True)
    
    # Gather the total grade for the submission and save it
    graderresultdf = pd.DataFrame([[submissionfile, gradingoutput.total, gradingoutput.possible]], 
                                  columns=["Submission Name", "Grade", "Possible"])

    # Gather the details of the grading
    detailedresults = []
    for exercisename, exercise in gradingoutput.results.items():
        testcasemessage = ""
        
        # Iterate over the test results to collect the feedback messages if any
        if includetestcasemessages:
            for test_case_result in exercise.test_case_results:
                # name
                testcasemessage += "Test " + test_case_result.test_case.name+" ("
                # hidden or public
                testcasemessage += "hidden, " if test_case_result.test_case.hidden else "public, "
                # passed or failed
                testcasemessage += "passed)" if test_case_result.passed else "failed)"
                # test case message
                if (test_case_result.passed and (test_case_result.test_case.success_message is not None)):
                    testcasemessage+= ": " + test_case_result.test_case.success_message
                elif ((not test_case_result.passed) and (test_case_result.test_case.failure_message is not None)):
                    testcasemessage+= ": " + test_case_result.test_case.failure_message
                testcasemessage += "\n"
        
        detailedresults.append([exercise.name, exercise.score, exercise.possible, testcasemessage])
    
    graderdetailsdf = pd.DataFrame(detailedresults, columns=["Exercise", "Grade", "Possible", "Feedback"])

    
    # Saving the results to CSV files
    # Creating the output folder if it does not exist
    if not os.path.exists(graderoutputfolder):
        os.mkdir(graderoutputfolder)

    # Saving the overall grade
    graderresultfile = graderoutputfolder+"/"+graderresultfilename+".csv"
    graderresultdf.to_csv(graderresultfile, index=False, quoting=csv.QUOTE_NONNUMERIC)

    # Saving the details
    graderdetailsfile = graderoutputfolder+"/"+graderdetailsfilename+".csv"
    graderdetailsdf.to_csv(graderdetailsfile, header=True, index=False, quoting=csv.QUOTE_NONNUMERIC)
    
        
    return graderresultdf, graderdetailsdf

def write_moodleCSV(moodlegradebookfile, graderresultdf, graderdetailsdf, 
                    includedetailsgrades=True, includedetailsmsgs=True):

    """
    Reads the moodle gradebook file corresponding to 1 submission and updates it with the result of the grading (grade and feedback message).
    Uses the dataframes produced by the `grade_and_writeCSV` function.

    Parameters:
    - moodlegradebookfile: path to the moodle gradebook file for this submission
    - graderresultdf: Pandas dataframe with the resulting grade for this submission (3 columns: "Submission Name", "Grade", "Possible")
    - graderdetailsdf: Pandas dataframe with the detailed output of the grading (4 columns: "Exercise", "Grade", "Possible", "Feedback")
    - includedetailsgrades: boolean indicating whether to include the details of the grading (points per exercises) - default is True
    - includedetailsmsgs: boolean indicating whether to include the messages generated by the grading (outputs of the tests) - default is True 

    Returns: 
    - moodledf: Pandas dataframe with the moodle information (10 columns: "Identifier", "Full name", "Email address", "Status", "Grade", "Maximum Grade", "Grade can be changed", 
    "Last modified (submission)", "Last modified (grade)", "Feedback comments")
    """

    # Read the moodle file
    moodledf = pd.read_csv(moodlegradebookfile, skip_blank_lines=True)
    #display(moodledf)
    
    if includedetailsgrades:
        # Formatters to get a pretty rendering of the info
        exerciseformatter = lambda x: 'Question %s:' % x
        gradeformatter = lambda x: '%s /' % x
        msgformatter = lambda x: '=> Messages: %s' % x.replace("\n", "; ")
        
        # Transform the details into string
        details = graderdetailsdf.to_string(index=False, header=False, 
                                         columns=["Exercise", "Grade", "Possible"] + (["Feedback"] if includedetailsmsgs else []),
                                         formatters={'Exercise': exerciseformatter, 'Grade': gradeformatter, 'Feedback': msgformatter})
        
        # Add the details to the moodle info
        moodledf.loc[0, "Feedback comments"] = details

        
    # Modify the moodle info
    moodledf.loc[0, "Grade"] = graderresultdf.loc[0, "Grade"]
    #moodledf.loc[0, "Maximum Grade"] = graderresultdf.loc[0, "Possible"] # Actually this line is useless, it is not used by moodle
    moodledf.loc[0, "Last modified (grade)"] = datetime.today().strftime('%A, %d %B %Y %H:%M') # This line is important for the file to be read by moodle!!!
    
    
    # Write the moodle file
    moodledf.to_csv(moodlegradebookfile, index=False, quoting=csv.QUOTE_NONNUMERIC) # The quotes are important for the file to be read by moodle
    
    return moodledf